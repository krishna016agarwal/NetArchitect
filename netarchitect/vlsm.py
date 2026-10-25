"""
vlsm.py — VLSM allocator for NetArchitect.
All subnet math uses integer bit operations. Does NOT import ipaddress.
"""
from netarchitect.models import SubnetAllocation, Decision
from netarchitect.errors import AddressSpaceExhaustedError


# ═══════════════════════════════════════════════════════════════════════════
# Helper functions — integer bit operations only
# ═══════════════════════════════════════════════════════════════════════════

def ip_to_int(ip_str: str) -> int:
    """Convert dotted-quad IP string to 32-bit integer."""
    parts = ip_str.split(".")
    return (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])


def int_to_ip(val: int) -> str:
    """Convert 32-bit integer to dotted-quad IP string."""
    return (f"{(val >> 24) & 0xFF}.{(val >> 16) & 0xFF}."
            f"{(val >> 8) & 0xFF}.{val & 0xFF}")


def prefix_to_mask_int(prefix_len: int) -> int:
    """Convert prefix length to subnet mask as integer."""
    if prefix_len == 0:
        return 0
    return (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF


def mask_to_wildcard_int(mask_int: int) -> int:
    """Convert subnet mask integer to wildcard mask integer."""
    return ~mask_int & 0xFFFFFFFF


def compute_block_size(hosts: int, is_ptp: bool = False,
                       is_loopback: bool = False,
                       allow_slash31: bool = False) -> int:
    """Compute the block size (number of addresses) for a subnet.

    - Loopback: block = 1 (/32)
    - PTP with allow_slash31: block = 2 (/31, RFC 3021, no +2)
    - PTP without allow_slash31: block = 4 (/30)
    - Regular: block = next power of 2 >= hosts + 2
    """
    if is_loopback:
        return 1
    if is_ptp:
        return 2 if allow_slash31 else 4
    needed = hosts + 2  # network + broadcast addresses
    if needed < 2:
        needed = 2
    host_bits = (needed - 1).bit_length()
    return 1 << host_bits


def block_to_prefix(block_size: int) -> int:
    """Convert a block size (power of 2) to prefix length."""
    n = (block_size).bit_length() - 1
    return 32 - n


# ═══════════════════════════════════════════════════════════════════════════
# Flat VLSM allocator
# ═══════════════════════════════════════════════════════════════════════════

def allocate_vlsm(root_prefix_str: str, requests: list,
                  allow_slash31: bool = False) -> tuple:
    """Allocate subnets from a root prefix using VLSM.

    Args:
        root_prefix_str: Root prefix in CIDR notation (e.g. "10.10.0.0/16")
        requests: List of dicts with keys:
            name, hosts, site, is_ptp (optional), is_loopback (optional)
        allow_slash31: Allow /31 for point-to-point links (RFC 3021)

    Returns:
        (list[SubnetAllocation], list[Decision])

    Raises:
        AddressSpaceExhaustedError: If allocations don't fit in root.
    """
    ip_str, plen_str = root_prefix_str.split("/")
    root_prefix_len = int(plen_str)
    root_mask = prefix_to_mask_int(root_prefix_len)
    root_network = ip_to_int(ip_str) & root_mask
    root_size = 1 << (32 - root_prefix_len)
    root_end = root_network + root_size  # exclusive

    # Build items with computed block sizes
    items = []
    for req in requests:
        is_ptp = req.get("is_ptp", False)
        is_lb = req.get("is_loopback", False)
        hosts = req.get("hosts", 0)
        block = compute_block_size(hosts, is_ptp, is_lb, allow_slash31)
        items.append({**req, "_block": block})

    # Sort descending by block size (stable sort, tie-break by name)
    items.sort(key=lambda x: (-x["_block"], x.get("name", "")))

    decisions = []
    decisions.append(Decision(
        rule_id="VLSM-001",
        domain="vlsm",
        subject="Allocation order",
        choice="Descending by block size",
        reason=(
            f"Sorted {len(items)} subnet requests in descending order by block "
            f"size to minimize address space fragmentation. Largest subnets are "
            f"allocated first, ensuring natural alignment without wasted gaps."
        ),
        references=["RFC 4632"],
    ))

    cursor = root_network
    allocations = []

    for item in items:
        size = item["_block"]
        is_ptp = item.get("is_ptp", False)
        is_lb = item.get("is_loopback", False)
        hosts = item.get("hosts", 0)
        name = item.get("name", "")
        site = item.get("site", "")

        # Align cursor up to block boundary
        cursor = (cursor + size - 1) & ~(size - 1) & 0xFFFFFFFF

        if cursor + size > root_end:
            raise AddressSpaceExhaustedError(
                requested=size,
                available=max(0, root_end - cursor),
                root_prefix=root_prefix_str,
            )

        network = cursor
        plen = block_to_prefix(size)
        mask_int = prefix_to_mask_int(plen)
        wildcard_int = mask_to_wildcard_int(mask_int)
        broadcast = network | wildcard_int

        if is_lb:
            gateway = int_to_ip(network)
            first_usable = gateway
            last_usable = gateway
            usable = 1
        elif is_ptp and allow_slash31:
            # RFC 3021: both addresses are usable, no network/broadcast
            gateway = int_to_ip(network)
            first_usable = int_to_ip(network)
            last_usable = int_to_ip(network + 1)
            usable = 2
        else:
            gateway = int_to_ip(network + 1)
            first_usable = int_to_ip(network + 1)
            if size > 2:
                last_usable = int_to_ip(broadcast - 1)
                usable = size - 2
            else:
                last_usable = first_usable
                usable = 0

        utilization = round(hosts / usable * 100, 1) if usable > 0 else 0.0

        alloc = SubnetAllocation(
            name=name, site=site, hosts_requested=hosts,
            network=int_to_ip(network), prefix_len=plen,
            mask=int_to_ip(mask_int), wildcard=int_to_ip(wildcard_int),
            broadcast=int_to_ip(broadcast), gateway=gateway,
            first_usable=first_usable, last_usable=last_usable,
            usable_count=usable, utilization=utilization,
            is_ptp=is_ptp, is_loopback=is_lb,
        )
        allocations.append(alloc)

        # Decision for this subnet
        if is_lb:
            reason = f"Loopback {name}: /32 host route, 1 address."
        elif is_ptp:
            slash = "/31 (RFC 3021)" if allow_slash31 else "/30"
            reason = (
                f"Point-to-point link {name}: {slash}, block size {size}. "
                f"{'RFC 3021 allows both addresses to be usable.' if allow_slash31 else 'Network + broadcast + 2 usable host addresses.'}"
            )
        else:
            host_bits = 32 - plen
            reason = (
                f"Subnet {name}: {hosts} hosts requested, need {hosts}+2 = "
                f"{hosts + 2} addresses, host bits = ceil(log2({hosts + 2})) = "
                f"{host_bits}, block size = 2^{host_bits} = {size}, prefix = /{plen}. "
                f"Usable = 2^{host_bits} - 2 = {usable}. "
                f"Utilization = {hosts}/{usable} = {utilization}%."
            )

        decisions.append(Decision(
            rule_id=f"VLSM-{len(decisions) + 1:03d}",
            domain="vlsm",
            subject=f"{name} ({site})",
            choice=f"{int_to_ip(network)}/{plen}",
            reason=reason,
            references=["RFC 4632"] + (["RFC 3021"] if is_ptp and allow_slash31 else []),
        ))

        cursor = network + size

    # Summary decision
    total_allocated = sum(a.usable_count for a in allocations)
    total_hosts = sum(a.hosts_requested for a in allocations)
    wasted = total_allocated - total_hosts
    efficiency = round(total_hosts / total_allocated * 100, 1) if total_allocated > 0 else 0
    decisions.append(Decision(
        rule_id="VLSM-SUMMARY",
        domain="vlsm",
        subject="Allocation summary",
        choice=f"{len(allocations)} subnets, {efficiency}% efficient",
        reason=(
            f"Allocated {len(allocations)} subnets: {total_hosts} hosts in "
            f"{total_allocated} usable addresses. Wasted: {wasted}. "
            f"Overall efficiency: {efficiency}%."
        ),
        references=["RFC 4632"],
    ))

    return allocations, decisions


# ═══════════════════════════════════════════════════════════════════════════
# Hierarchical VLSM allocator (multi-site)
# ═══════════════════════════════════════════════════════════════════════════

def _next_power_of_2(n: int) -> int:
    """Return the smallest power of 2 >= n."""
    if n <= 0:
        return 1
    return 1 << (n - 1).bit_length()


def allocate_hierarchical(root_prefix_str: str, sites_requests: dict,
                          ptp_requests: list = None,
                          loopback_requests: list = None,
                          allow_slash31: bool = False) -> tuple:
    """Hierarchical VLSM: allocate per-site aggregates, then VLSM within each.

    Args:
        root_prefix_str: Root prefix (e.g. "10.100.0.0/16")
        sites_requests: {site_name: [request_dicts]} — VLANs grouped by site
        ptp_requests: Point-to-point link requests (allocated from infra space)
        loopback_requests: Loopback requests (allocated from infra space)
        allow_slash31: Allow /31 for PTP

    Returns:
        (list[SubnetAllocation], list[Decision])
    """
    if ptp_requests is None:
        ptp_requests = []
    if loopback_requests is None:
        loopback_requests = []

    ip_str, plen_str = root_prefix_str.split("/")
    root_prefix_len = int(plen_str)
    root_mask = prefix_to_mask_int(root_prefix_len)
    root_network = ip_to_int(ip_str) & root_mask
    root_size = 1 << (32 - root_prefix_len)
    root_end = root_network + root_size

    decisions = []
    all_allocations = []

    # Step 1: Compute per-site aggregate sizes
    site_aggregates = {}
    for site_name, reqs in sites_requests.items():
        total_blocks = 0
        for req in reqs:
            block = compute_block_size(req["hosts"], req.get("is_ptp", False),
                                       req.get("is_loopback", False), allow_slash31)
            total_blocks += block
        agg_size = _next_power_of_2(total_blocks)
        site_aggregates[site_name] = agg_size

    # Sort aggregates descending by size
    sorted_sites = sorted(site_aggregates.items(), key=lambda x: (-x[1], x[0]))

    # Step 2: Allocate aggregates from root
    cursor = root_network
    agg_allocs = {}  # site -> (network_int, size, prefix_len)

    for site_name, agg_size in sorted_sites:
        cursor = (cursor + agg_size - 1) & ~(agg_size - 1) & 0xFFFFFFFF
        if cursor + agg_size > root_end:
            raise AddressSpaceExhaustedError(agg_size, max(0, root_end - cursor),
                                              root_prefix_str)
        agg_prefix = block_to_prefix(agg_size)
        agg_allocs[site_name] = (cursor, agg_size, agg_prefix)

        decisions.append(Decision(
            rule_id=f"VLSM-AGG-{site_name}",
            domain="vlsm",
            subject=f"Site aggregate: {site_name}",
            choice=f"{int_to_ip(cursor)}/{agg_prefix}",
            reason=(
                f"Site {site_name} aggregate: total subnet blocks = "
                f"{sum(compute_block_size(r['hosts'], r.get('is_ptp', False), r.get('is_loopback', False), allow_slash31) for r in sites_requests[site_name])}, "
                f"rounded up to next power of 2 = {agg_size} "
                f"(/{agg_prefix}). This aggregate serves as the OSPF area-range "
                f"summary address for {site_name}."
            ),
            references=["RFC 4632", "RFC 2328"],
        ))
        cursor += agg_size

    # Step 3: VLSM within each aggregate
    for site_name, agg_size in sorted_sites:
        agg_net, agg_sz, agg_plen = agg_allocs[site_name]
        agg_prefix_str = f"{int_to_ip(agg_net)}/{agg_plen}"
        site_allocs, site_decisions = allocate_vlsm(
            agg_prefix_str, sites_requests[site_name], allow_slash31)
        # Tag with aggregate
        for a in site_allocs:
            a.aggregate_prefix = agg_prefix_str
        all_allocations.extend(site_allocs)
        decisions.extend(site_decisions)

    # Step 4: Infrastructure (PTP + loopbacks) from remaining space
    infra_requests = ptp_requests + loopback_requests
    if infra_requests:
        infra_cursor = cursor
        # Use remaining root space for infra
        remaining_size = root_end - infra_cursor
        if remaining_size > 0:
            # Find the prefix that covers remaining_size
            remaining_prefix = 32 - max(1, (remaining_size).bit_length() - 1)
            # Align
            aligned_size = 1 << (32 - remaining_prefix)
            infra_cursor = (infra_cursor + aligned_size - 1) & ~(aligned_size - 1) & 0xFFFFFFFF
            if infra_cursor + aligned_size <= root_end:
                infra_prefix = f"{int_to_ip(infra_cursor)}/{remaining_prefix}"
                infra_allocs, infra_decs = allocate_vlsm(
                    infra_prefix, infra_requests, allow_slash31)
                for a in infra_allocs:
                    a.aggregate_prefix = infra_prefix
                all_allocations.extend(infra_allocs)
                decisions.extend(infra_decs)
            else:
                # Try with a smaller block
                for req in infra_requests:
                    block = compute_block_size(
                        req.get("hosts", 0), req.get("is_ptp", False),
                        req.get("is_loopback", False), allow_slash31)
                    infra_cursor = (infra_cursor + block - 1) & ~(block - 1) & 0xFFFFFFFF
                    if infra_cursor + block > root_end:
                        raise AddressSpaceExhaustedError(block, max(0, root_end - infra_cursor),
                                                          root_prefix_str)
                    plen = block_to_prefix(block)
                    mask_int = prefix_to_mask_int(plen)
                    wildcard_int = mask_to_wildcard_int(mask_int)
                    broadcast = infra_cursor | wildcard_int
                    is_lb = req.get("is_loopback", False)
                    is_ptp = req.get("is_ptp", False)
                    if is_lb:
                        gw = int_to_ip(infra_cursor)
                        fu = lu = gw
                        usable = 1
                    elif is_ptp and allow_slash31:
                        gw = int_to_ip(infra_cursor)
                        fu = gw
                        lu = int_to_ip(infra_cursor + 1)
                        usable = 2
                    else:
                        gw = int_to_ip(infra_cursor + 1)
                        fu = gw
                        lu = int_to_ip(broadcast - 1) if block > 2 else gw
                        usable = block - 2
                    hosts = req.get("hosts", 0)
                    util = round(hosts / usable * 100, 1) if usable > 0 else 0.0
                    all_allocations.append(SubnetAllocation(
                        name=req.get("name", ""), site=req.get("site", ""),
                        hosts_requested=hosts,
                        network=int_to_ip(infra_cursor), prefix_len=plen,
                        mask=int_to_ip(mask_int), wildcard=int_to_ip(wildcard_int),
                        broadcast=int_to_ip(broadcast), gateway=gw,
                        first_usable=fu, last_usable=lu,
                        usable_count=usable, utilization=util,
                        is_ptp=is_ptp, is_loopback=is_lb,
                    ))
                    infra_cursor += block

    return all_allocations, decisions

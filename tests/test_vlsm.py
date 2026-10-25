"""
test_vlsm.py — Comprehensive VLSM allocator test suite using ipaddress as oracle.
Tests:
  - 1000 seeded random request lists with zero subnet overlaps
  - Every subnet aligned to its block size and contained inside root
  - Usable hosts >= requested
  - Address space exhaustion
  - Edge cases: hosts = 1, 2, 254, 255, 256
  - Subnet boundaries: /30, /31 (RFC 3021), /32
"""
import random
import ipaddress
import pytest
from netarchitect.vlsm import (
    allocate_vlsm,
    compute_block_size,
    block_to_prefix,
    allocate_hierarchical,
)
from netarchitect.errors import AddressSpaceExhaustedError


def test_vlsm_1000_seeded_random_scenarios_no_overlaps():
    """Run 1000 randomized allocation scenarios.
    Using ipaddress as oracle, verify:
      1. No subnets overlap.
      2. Every subnet is contained inside root.
      3. Every subnet is aligned to its block size boundary.
      4. Usable host count >= requested host count.
    """
    rng = random.Random(42)
    root_cidr = "10.0.0.0/20"  # 4096 addresses
    oracle_root = ipaddress.IPv4Network(root_cidr)

    for trial in range(1000):
        # Generate 3 to 10 random requests with host counts 2 to 200
        num_reqs = rng.randint(3, 10)
        requests = [
            {"name": f"Subnet_{i}", "hosts": rng.randint(2, 200), "site": "SiteA"}
            for i in range(num_reqs)
        ]

        allocations, _ = allocate_vlsm(root_cidr, requests)

        oracle_subnets = []
        for alloc in allocations:
            net = ipaddress.IPv4Network(f"{alloc.network}/{alloc.prefix_len}")
            oracle_subnets.append(net)

            # Inside root
            assert net.subnet_of(oracle_root), f"Subnet {net} outside root {oracle_root}"

            # Boundary alignment
            block_size = 1 << (32 - alloc.prefix_len)
            assert int(net.network_address) % block_size == 0, (
                f"Subnet {net} unaligned to block size {block_size}"
            )

            # Usable hosts check
            assert alloc.usable_count >= alloc.hosts_requested

        # Pairwise overlap check
        for i in range(len(oracle_subnets)):
            for j in range(i + 1, len(oracle_subnets)):
                assert not oracle_subnets[i].overlaps(oracle_subnets[j]), (
                    f"Trial {trial}: Overlap between {oracle_subnets[i]} and {oracle_subnets[j]}"
                )


def test_address_space_exhaustion():
    """Requesting more addresses than available in root prefix raises AddressSpaceExhaustedError."""
    root_cidr = "192.168.1.0/24"  # 256 addresses
    requests = [
        {"name": "Subnet_Large1", "hosts": 150, "site": "HQ"},
        {"name": "Subnet_Large2", "hosts": 150, "site": "HQ"},
    ]
    with pytest.raises(AddressSpaceExhaustedError) as exc_info:
        allocate_vlsm(root_cidr, requests)
    assert "Address space exhausted" in str(exc_info.value)
    assert "192.168.1.0/24" in str(exc_info.value)


@pytest.mark.parametrize("hosts,expected_block,expected_prefix,expected_usable", [
    (1, 4, 30, 2),        # host=1 needs block 4 (/30), 2 usable
    (2, 4, 30, 2),        # host=2 needs block 4 (/30), 2 usable
    (254, 256, 24, 254),  # host=254 fits in /24 (256 - 2 = 254)
    (255, 512, 23, 510),  # host=255 requires /23
    (256, 512, 23, 510),  # host=256 requires /23 (needs 258 addresses)
])
def test_host_boundary_block_sizes(hosts, expected_block, expected_prefix, expected_usable):
    """Verify exact block sizes, prefixes and usable counts for boundary host numbers."""
    block = compute_block_size(hosts)
    prefix = block_to_prefix(block)
    usable = block - 2
    assert block == expected_block
    assert prefix == expected_prefix
    assert usable == expected_usable


def test_slash31_and_slash32_edge_cases():
    """Verify /31 PTP links (RFC 3021) and /32 Loopbacks."""
    # /31 PTP
    ptp_block = compute_block_size(2, is_ptp=True, allow_slash31=True)
    assert ptp_block == 2
    assert block_to_prefix(ptp_block) == 31

    # /30 PTP (default)
    ptp30_block = compute_block_size(2, is_ptp=True, allow_slash31=False)
    assert ptp30_block == 4
    assert block_to_prefix(ptp30_block) == 30

    # /32 Loopback
    lb_block = compute_block_size(1, is_loopback=True)
    assert lb_block == 1
    assert block_to_prefix(lb_block) == 32


def test_hierarchical_allocation():
    """Hierarchical multi-site allocation creates non-overlapping site aggregate summaries."""
    sites_requests = {
        "SiteA": [{"name": "A_Users", "hosts": 100, "site": "SiteA"}],
        "SiteB": [{"name": "B_Users", "hosts": 200, "site": "SiteB"}],
    }
    ptp_reqs = [{"name": "P2P-A-B", "hosts": 2, "site": "SiteA", "is_ptp": True}]
    loopbacks = [{"name": "Lo0-R1", "hosts": 1, "site": "SiteA", "is_loopback": True}]

    allocs, decs = allocate_hierarchical("10.10.0.0/16", sites_requests, ptp_reqs, loopbacks)
    oracle_nets = [ipaddress.IPv4Network(f"{a.network}/{a.prefix_len}") for a in allocs]

    for i in range(len(oracle_nets)):
        for j in range(i + 1, len(oracle_nets)):
            assert not oracle_nets[i].overlaps(oracle_nets[j])

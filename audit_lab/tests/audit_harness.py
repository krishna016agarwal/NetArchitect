"""
Audit Harness — Independent checker for AI first-draft solutions.
Uses ipaddress module as ground truth oracle.
Never modifies the drafts. Reports PASS/FAIL for each check.
"""
import sys
import os
import ipaddress
import importlib.util
import re
import math

# ── Paths ──────────────────────────────────────────────────────────────────
AUDIT_DIR = os.path.dirname(os.path.abspath(__file__))
DRAFTS_DIR = os.path.join(os.path.dirname(AUDIT_DIR), "ai_drafts")

results = []  # (task, check_name, passed, expected, actual)


def record(task, check, passed, expected=None, actual=None):
    results.append((task, check, passed, expected, actual))
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] Task {task}: {check}"
    if not passed:
        msg += f"\n    Expected: {expected}\n    Actual:   {actual}"
    print(msg)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ══════════════════════════════════════════════════════════════════════════
# TASK 01: Wildcard mask and broadcast for all prefixes /0 to /32
# ══════════════════════════════════════════════════════════════════════════
def test_01_wildcard():
    mod = load_module(os.path.join(DRAFTS_DIR, "01_wildcard.py"), "wildcard01")
    fn = mod.wildcard_and_broadcast

    test_ips = [
        "10.0.0.0", "192.168.1.0", "172.16.0.0", "255.255.255.255",
        "0.0.0.0", "10.10.1.64",
    ]

    for prefix_len in range(0, 33):
        for ip_str in test_ips:
            cidr = f"{ip_str}/{prefix_len}"
            try:
                net = ipaddress.IPv4Network(cidr, strict=False)
            except Exception:
                continue  # skip if ipaddress can't parse

            try:
                result = fn(cidr)
            except Exception as e:
                record("01", f"wildcard {cidr} raised exception", False,
                       "valid result", str(e))
                continue

            # Expected values from ipaddress
            expected_wildcard = str(net.hostmask)
            expected_broadcast = str(net.broadcast_address)
            expected_network = str(net.network_address)
            expected_mask = str(net.netmask)

            if result['wildcard'] != expected_wildcard:
                record("01", f"wildcard for {cidr}", False,
                       expected_wildcard, result['wildcard'])
            else:
                record("01", f"wildcard for {cidr}", True)

            if result['broadcast'] != expected_broadcast:
                record("01", f"broadcast for {cidr}", False,
                       expected_broadcast, result['broadcast'])
            else:
                record("01", f"broadcast for {cidr}", True)

            if result['network'] != expected_network:
                record("01", f"network for {cidr}", False,
                       expected_network, result['network'])
            else:
                record("01", f"network for {cidr}", True)

            if result['mask'] != expected_mask:
                record("01", f"mask for {cidr}", False,
                       expected_mask, result['mask'])
            else:
                record("01", f"mask for {cidr}", True)

    # Specific edge cases: /31 and /32
    for edge_cidr in ["10.10.1.64/31", "10.10.1.64/32", "0.0.0.0/0"]:
        net = ipaddress.IPv4Network(edge_cidr, strict=False)
        try:
            result = fn(edge_cidr)
            record("01", f"/31-/32 edge {edge_cidr} wildcard", 
                   result['wildcard'] == str(net.hostmask),
                   str(net.hostmask), result['wildcard'])
            record("01", f"/31-/32 edge {edge_cidr} broadcast",
                   result['broadcast'] == str(net.broadcast_address),
                   str(net.broadcast_address), result['broadcast'])
        except Exception as e:
            record("01", f"/31-/32 edge {edge_cidr}", False,
                   "valid result", str(e))


# ══════════════════════════════════════════════════════════════════════════
# TASK 02: VLSM allocator checks
# ══════════════════════════════════════════════════════════════════════════
def test_02_vlsm():
    mod = load_module(os.path.join(DRAFTS_DIR, "02_vlsm.py"), "vlsm02")
    fn = mod.vlsm_allocate

    # ── Basic allocation check ──
    root_cidr = "192.168.1.0/24"
    host_counts = [50, 20, 100, 10]
    try:
        result = fn(root_cidr, host_counts)
    except Exception as e:
        record("02", "basic allocation raised exception", False,
               "valid result", str(e))
        return

    root_net = ipaddress.IPv4Network(root_cidr, strict=False)

    # Check: no overlaps
    subnets_ip = []
    for r in result:
        net = ipaddress.IPv4Network(f"{r['network']}/{r['prefix']}", strict=False)
        subnets_ip.append(net)

    overlap_found = False
    for i, s1 in enumerate(subnets_ip):
        for j, s2 in enumerate(subnets_ip):
            if i < j and s1.overlaps(s2):
                overlap_found = True
                record("02", f"no overlap between subnet {i} and {j}", False,
                       "no overlap", f"{s1} overlaps {s2}")
    if not overlap_found:
        record("02", "no overlaps in basic allocation", True)

    # Check: each subnet aligned to its block size
    alignment_ok = True
    for r in result:
        net_int = int(ipaddress.IPv4Address(r['network']))
        block_size = 2 ** (32 - r['prefix'])
        if net_int % block_size != 0:
            record("02", f"alignment for {r['network']}/{r['prefix']}", False,
                   f"aligned to {block_size}", f"network {net_int} % {block_size} = {net_int % block_size}")
            alignment_ok = False
    if alignment_ok:
        record("02", "all subnets aligned", True)

    # Check: usable hosts >= request
    for r in result:
        if r['usable'] < r['hosts_requested']:
            record("02", f"usable >= requested for {r['network']}", False,
                   f">= {r['hosts_requested']}", r['usable'])
        else:
            record("02", f"usable >= requested for {r['network']}", True)

    # Check: all inside root
    for r in result:
        net = ipaddress.IPv4Network(f"{r['network']}/{r['prefix']}", strict=False)
        if not (net.network_address >= root_net.network_address and
                net.broadcast_address <= root_net.broadcast_address):
            record("02", f"inside root for {r['network']}", False,
                   f"inside {root_cidr}", str(net))
        else:
            record("02", f"inside root for {r['network']}", True)

    # ── Exhaustion behavior ──
    try:
        fn("192.168.1.0/24", [300])
        record("02", "exhaustion raises error", False,
               "ValueError or similar", "no exception raised")
    except (ValueError, Exception):
        record("02", "exhaustion raises error", True)

    # ── Unsorted input ──
    try:
        result_unsorted = fn("10.0.0.0/16", [10, 500, 30, 200, 5])
        # Verify descending sort: each block should be >= next block
        sizes = [2 ** (32 - r['prefix']) for r in result_unsorted]
        sorted_ok = all(sizes[i] >= sizes[i + 1] for i in range(len(sizes) - 1))
        record("02", "descending sort with unsorted input", sorted_ok,
               "sorted descending", sizes)
    except Exception as e:
        record("02", "unsorted input raised exception", False,
               "valid result", str(e))

    # ── Edge cases: host counts 0, 1, 2 ──
    for hc in [0, 1, 2]:
        try:
            result_edge = fn("10.0.0.0/24", [hc])
            if len(result_edge) > 0:
                r = result_edge[0]
                # hosts=0 -> block_size should be 2 (net+bcast), usable=0 -> /31 or /30
                # hosts=1 -> block_size=4 minimum (/30), usable=2
                # hosts=2 -> block_size=4 (/30), usable=2
                record("02", f"edge case hosts={hc} runs", True)
                # Verify usable >= hc
                if r['usable'] < hc:
                    record("02", f"edge hosts={hc} usable >= {hc}", False,
                           f">= {hc}", r['usable'])
                else:
                    record("02", f"edge hosts={hc} usable >= {hc}", True)
            else:
                record("02", f"edge case hosts={hc}", False,
                       "at least one result", "empty list")
        except Exception as e:
            record("02", f"edge case hosts={hc} raised exception", False,
                   "valid result", str(e))


# ══════════════════════════════════════════════════════════════════════════
# TASK 03: Optical budget check
# Independent calculation using the spec's OPTICAL CONSTANTS.
# ══════════════════════════════════════════════════════════════════════════
def test_03_optical():
    mod = load_module(os.path.join(DRAFTS_DIR, "03_optical.py"), "optical03")
    fn = mod.check_optical_budget

    # Reference OPTICAL CONSTANTS from the spec:
    # LR: 1310 nm, reach 10 km, Tx_min -8.2 dBm, Rx_sens -14.4 dBm
    # ER: 1550 nm, 40 km, -4.7, -15.8
    # Budget = Tx_min - Rx_sens
    # Loss = km * attenuation + 4 connectors * 0.5 dB + floor(km/2) * 0.1 dB splices + 2 dB safety
    # Attenuation: 0.35 dB/km at 1310 nm, 0.25 dB/km at 1550 nm
    # Margin = Budget - Loss

    def reference_calc(link_type, distance_km):
        specs = {
            'LR': {'wavelength': 1310, 'tx_min': -8.2, 'rx_sens': -14.4},
            'ER': {'wavelength': 1550, 'tx_min': -4.7, 'rx_sens': -15.8},
        }
        s = specs[link_type]
        budget = s['tx_min'] - s['rx_sens']

        att_per_km = 0.35 if s['wavelength'] == 1310 else 0.25
        fiber_loss = distance_km * att_per_km
        connector_loss = 4 * 0.5  # 4 connectors, 0.5 dB each
        splice_loss = math.floor(distance_km / 2) * 0.1
        safety = 2.0

        total_loss = fiber_loss + connector_loss + splice_loss + safety
        margin = budget - total_loss
        feasible = margin >= 0
        return {
            'budget': round(budget, 2),
            'total_loss': round(total_loss, 2),
            'margin': round(margin, 2),
            'feasible': feasible,
        }

    # Test case 1: 35 km ER link
    ref = reference_calc('ER', 35)
    try:
        draft = fn('ER', 35)
        # Check budget
        record("03", "ER 35km budget", 
               abs(draft['budget_dB'] - ref['budget']) < 0.01,
               ref['budget'], draft['budget_dB'])
        # Check total loss
        record("03", "ER 35km total_loss",
               abs(draft['total_loss_dB'] - ref['total_loss']) < 0.01,
               ref['total_loss'], draft['total_loss_dB'])
        # Check margin
        record("03", "ER 35km margin",
               abs(draft['margin_dB'] - ref['margin']) < 0.01,
               ref['margin'], draft['margin_dB'])
        # Check feasibility
        record("03", "ER 35km feasible",
               draft['feasible'] == ref['feasible'],
               ref['feasible'], draft['feasible'])
    except Exception as e:
        record("03", "ER 35km raised exception", False, "valid result", str(e))

    # Test case 2: 8 km LR link
    ref = reference_calc('LR', 8)
    try:
        draft = fn('LR', 8)
        record("03", "LR 8km budget",
               abs(draft['budget_dB'] - ref['budget']) < 0.01,
               ref['budget'], draft['budget_dB'])
        record("03", "LR 8km total_loss",
               abs(draft['total_loss_dB'] - ref['total_loss']) < 0.01,
               ref['total_loss'], draft['total_loss_dB'])
        record("03", "LR 8km margin",
               abs(draft['margin_dB'] - ref['margin']) < 0.01,
               ref['margin'], draft['margin_dB'])
        record("03", "LR 8km feasible",
               draft['feasible'] == ref['feasible'],
               ref['feasible'], draft['feasible'])
    except Exception as e:
        record("03", "LR 8km raised exception", False, "valid result", str(e))


# ══════════════════════════════════════════════════════════════════════════
# TASK 04: IOS access switch config checks
# ══════════════════════════════════════════════════════════════════════════
def test_04_switch():
    config_path = os.path.join(DRAFTS_DIR, "04_switch.txt")
    with open(config_path, 'r') as f:
        config = f.read()
    
    lines = [line.strip() for line in config.splitlines() if line.strip() and not line.strip().startswith('!')]

    # Check: trunk has an explicit "switchport trunk allowed vlan" list
    has_trunk_allowed_vlan = any("switchport trunk allowed vlan" in line for line in lines)
    record("04", "trunk has explicit 'switchport trunk allowed vlan' list",
           has_trunk_allowed_vlan,
           "switchport trunk allowed vlan <list>",
           "not found" if not has_trunk_allowed_vlan else "found")

    # Check: native VLAN is not 1
    native_vlan_lines = [line for line in lines if "native vlan" in line.lower()]
    if not native_vlan_lines:
        # No native vlan set means it defaults to VLAN 1
        record("04", "native VLAN is not 1",
               False, "explicit native vlan != 1", "no native vlan set (defaults to 1)")
    else:
        native_ok = True
        for nvl in native_vlan_lines:
            match = re.search(r'native\s+vlan\s+(\d+)', nvl, re.IGNORECASE)
            if match and match.group(1) == '1':
                native_ok = False
        record("04", "native VLAN is not 1", native_ok,
               "native vlan != 1", native_vlan_lines)

    # Check: bpduguard on access ports
    has_bpduguard = any("bpduguard" in line.lower() for line in lines)
    record("04", "access ports have bpduguard", has_bpduguard,
           "spanning-tree bpduguard enable", 
           "found" if has_bpduguard else "not found")


# ══════════════════════════════════════════════════════════════════════════
# TASK 05: OSPF config checks
# ══════════════════════════════════════════════════════════════════════════
def test_05_ospf():
    config_path = os.path.join(DRAFTS_DIR, "05_ospf.txt")
    with open(config_path, 'r') as f:
        config = f.read()

    lines = [line.strip() for line in config.splitlines() if line.strip()]

    # Parse interface subnets from ip address commands
    interface_subnets = {}
    current_iface = None
    for line in lines:
        iface_match = re.match(r'interface\s+(\S+)', line, re.IGNORECASE)
        if iface_match:
            current_iface = iface_match.group(1)
        ip_match = re.match(r'ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)', line)
        if ip_match and current_iface:
            ip_addr = ip_match.group(1)
            mask = ip_match.group(2)
            iface_net = ipaddress.IPv4Network(f"{ip_addr}/{mask}", strict=False)
            interface_subnets[current_iface] = iface_net

    # Parse OSPF network statements
    network_stmts = []
    for line in lines:
        net_match = re.match(
            r'network\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+area\s+(\d+)',
            line, re.IGNORECASE
        )
        if net_match:
            network_stmts.append({
                'network': net_match.group(1),
                'wildcard': net_match.group(2),
                'area': net_match.group(3),
            })

    # The expected interface subnets:
    # 10.10.1.0/26 -> network 10.10.1.0, wildcard 0.0.0.63
    # 10.10.1.64/27 -> network 10.10.1.64, wildcard 0.0.0.31
    expected_subnets = {
        '10.10.1.0': {
            'prefix': 26,
            'wildcard': '0.0.0.63',
        },
        '10.10.1.64': {
            'prefix': 27,
            'wildcard': '0.0.0.31',
        },
    }

    # Check: OSPF network statements use wildcard masks that match each interface subnet
    for stmt in network_stmts:
        net_addr = stmt['network']
        if net_addr in expected_subnets:
            expected_wc = expected_subnets[net_addr]['wildcard']
            actual_wc = stmt['wildcard']
            record("05", f"OSPF wildcard for {net_addr}",
                   actual_wc == expected_wc,
                   expected_wc, actual_wc)
        else:
            # Network statement doesn't correspond to a known interface
            record("05", f"OSPF network {net_addr} matches an interface",
                   False, "known interface network", net_addr)

    # Check: all expected networks have OSPF statements
    for net_addr in expected_subnets:
        found = any(s['network'] == net_addr for s in network_stmts)
        record("05", f"OSPF network statement exists for {net_addr}",
               found, f"network {net_addr} in OSPF", "not found" if not found else "found")

    # Check: LAN-facing interfaces are passive
    has_passive = any("passive-interface" in line.lower() for line in lines)
    # Both interfaces in this case are LAN-facing, so they should be passive
    record("05", "LAN-facing interfaces are passive",
           has_passive,
           "passive-interface on LAN interfaces",
           "found" if has_passive else "not found")


# ══════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("=" * 72)
    print("  AUDIT HARNESS — Independent checks on AI first-draft solutions")
    print("=" * 72)
    print()

    test_01_wildcard()
    print()
    test_02_vlsm()
    print()
    test_03_optical()
    print()
    test_04_switch()
    print()
    test_05_ospf()

    print()
    print("=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    
    total = len(results)
    passed = sum(1 for r in results if r[2])
    failed = total - passed

    # Group failures by task
    failed_tasks = set()
    print(f"\nTotal checks: {total}  |  Passed: {passed}  |  Failed: {failed}")
    print()

    if failed > 0:
        print("FAILED CHECKS:")
        print("-" * 60)
        for task, check, ok, expected, actual in results:
            if not ok:
                failed_tasks.add(task)
                print(f"  Task {task}: {check}")
                print(f"    Expected: {expected}")
                print(f"    Actual:   {actual}")
                print()
    
    print(f"Tasks with failures: {sorted(failed_tasks) if failed_tasks else 'none'}")
    print()

    if len(failed_tasks) >= 2:
        print(f"✓ {len(failed_tasks)} tasks have real failures → valid audit candidates.")
        print(f"Audit candidate tasks: {sorted(failed_tasks)}")
    else:
        print(f"Only {len(failed_tasks)} task(s) failed. Fewer than 2 real failures.")

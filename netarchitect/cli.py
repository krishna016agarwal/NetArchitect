"""
cli.py — CLI entry point for NetArchitect.
Run: python -m netarchitect run --preset campus|metro|wan --out out/
"""
import argparse
import sys
import json

from netarchitect.errors import NetArchitectError
from netarchitect.inputs import load_preset, load_json
from netarchitect.media import select_media
from netarchitect.vlsm import allocate_vlsm, allocate_hierarchical
from netarchitect.routing import select_routing
from netarchitect.configgen import generate_all_configs
from netarchitect.exporter import export_all


def run_scenario(scenario, out_dir: str):
    """Execute the full NetArchitect pipeline for a scenario."""
    decisions = []

    # ── Phase 2: Media selection ──
    media_results = []
    for link in scenario.links:
        selection, link_decisions = select_media(
            link.a, link.b, link.distance_m,
            link.media_request, scenario.profile,
        )
        media_results.append(selection)
        decisions.extend(link_decisions)

    # ── Phase 3: VLSM allocation ──
    # Build requests from VLANs
    vlan_requests = [
        {"name": v.name, "hosts": v.hosts, "site": v.site}
        for v in scenario.vlans
    ]

    # PTP link requests
    ptp_requests = []
    for link in scenario.links:
        ptp_requests.append({
            "name": f"P2P-{link.a}-{link.b}",
            "hosts": 2,
            "site": link.a,
            "is_ptp": True,
        })

    # Loopback requests
    loopback_requests = []
    for site in scenario.sites:
        for device in site.devices:
            loopback_requests.append({
                "name": f"Lo0-{device.name}",
                "hosts": 1,
                "site": site.name,
                "is_loopback": True,
            })

    allow_slash31 = scenario.extras.get("allow_slash31", False)

    if scenario.profile == "wan" or (len(scenario.sites) > 1 and
                                      any(s.area is not None for s in scenario.sites)):
        # Hierarchical mode
        sites_vlans = {}
        for req in vlan_requests:
            sites_vlans.setdefault(req["site"], []).append(req)
        allocations, vlsm_decisions = allocate_hierarchical(
            scenario.root_prefix, sites_vlans,
            ptp_requests, loopback_requests, allow_slash31,
        )
    else:
        # Flat mode
        all_requests = vlan_requests + ptp_requests + loopback_requests
        allocations, vlsm_decisions = allocate_vlsm(
            scenario.root_prefix, all_requests, allow_slash31,
        )
    decisions.extend(vlsm_decisions)

    # ── Phase 4: Routing selection ──
    routing_config, routing_decisions = select_routing(scenario, allocations)
    decisions.extend(routing_decisions)

    # ── Config generation ──
    device_configs, config_decisions = generate_all_configs(
        scenario, allocations, media_results, routing_config,
    )
    decisions.extend(config_decisions)

    # ── Export ──
    profile_dir = export_all(
        out_dir, scenario, device_configs, decisions, allocations, media_results,
    )

    # ── Console summary ──
    print(f"NetArchitect — {scenario.profile.upper()} profile")
    print(f"{'=' * 60}")
    print(f"Decisions: {len(decisions)}")
    print(f"Subnets: {len(allocations)}")
    total_hosts = sum(a.hosts_requested for a in allocations)
    total_usable = sum(a.usable_count for a in allocations)
    eff = round(total_hosts / total_usable * 100, 1) if total_usable > 0 else 0
    print(f"Hosts: {total_hosts} / {total_usable} usable ({eff}% efficient)")
    print(f"\nSubnet allocation:")
    print(f"  {'Name':<25} {'Network':<18} {'Prefix':<8} {'Hosts':<8} {'Usable':<8}")
    print(f"  {'-'*25} {'-'*18} {'-'*8} {'-'*8} {'-'*8}")
    for a in allocations:
        print(f"  {a.name:<25} {a.network:<18} /{a.prefix_len:<7} {a.hosts_requested:<8} {a.usable_count:<8}")
    print(f"\nDevices: {len(device_configs)}")
    for name in device_configs:
        print(f"  - {name}")
    print(f"\nOutput: {profile_dir}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="netarchitect",
        description="NetArchitect — Network design CLI tool for CIC-307",
    )
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Run network design")
    group = run_parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preset", choices=["campus", "metro", "wan"],
                       help="Use a built-in preset")
    group.add_argument("--custom", type=str,
                       help="Path to a custom scenario JSON file")
    run_parser.add_argument("--out", type=str, default="out",
                            help="Output directory (default: out)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    try:
        if args.preset:
            scenario = load_preset(args.preset)
        else:
            scenario = load_json(args.custom)
        code = run_scenario(scenario, args.out)
        sys.exit(code)
    except NetArchitectError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

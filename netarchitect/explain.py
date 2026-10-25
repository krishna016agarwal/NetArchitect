"""
explain.py — Explainability engine for NetArchitect.
Collects Decision objects and produces rationale.md.
"""
from netarchitect.models import Decision


def build_rationale(decisions: list, allocations: list) -> str:
    """Build rationale.md content from decisions and allocations.

    Groups decisions by domain, adds summary table on top.
    """
    lines = []
    lines.append("# NetArchitect Design Rationale\n")
    lines.append("## Summary Table\n")
    lines.append("| # | Domain | Subject | Choice | References |")
    lines.append("|---|--------|---------|--------|------------|")
    for i, d in enumerate(decisions, 1):
        refs = ", ".join(d.references) if d.references else "-"
        lines.append(f"| {i} | {d.domain} | {d.subject} | {d.choice} | {refs} |")
    lines.append("")

    # Group by domain
    domains = {}
    for d in decisions:
        domains.setdefault(d.domain, []).append(d)

    for domain, decs in domains.items():
        lines.append(f"## {domain.upper()} Decisions\n")
        for d in decs:
            lines.append(f"### [{d.rule_id}] {d.subject}\n")
            lines.append(f"**Choice:** {d.choice}\n")
            lines.append(f"**Reason:** {d.reason}\n")
            if d.references:
                lines.append(f"**References:** {', '.join(d.references)}\n")
            lines.append("")

    # Allocation table
    if allocations:
        lines.append("## Subnet Allocation Table\n")
        lines.append("| Name | Site | Network | Prefix | Hosts | Usable | Util% | Gateway |")
        lines.append("|------|------|---------|--------|-------|--------|-------|---------|")
        total_hosts = 0
        total_usable = 0
        for a in allocations:
            lines.append(
                f"| {a.name} | {a.site} | {a.network} | /{a.prefix_len} | "
                f"{a.hosts_requested} | {a.usable_count} | {a.utilization}% | {a.gateway} |"
            )
            total_hosts += a.hosts_requested
            total_usable += a.usable_count
        wasted = total_usable - total_hosts
        eff = round(total_hosts / total_usable * 100, 1) if total_usable > 0 else 0
        lines.append(f"| **TOTAL** | | | | **{total_hosts}** | **{total_usable}** | **{eff}%** | |")
        lines.append(f"\n*Wasted addresses: {wasted}*\n")

    return "\n".join(lines)


def build_allocation_csv(allocations: list) -> str:
    """Build allocation.csv content."""
    rows = ["Name,Site,Network,Prefix,Mask,Wildcard,Broadcast,Gateway,FirstUsable,LastUsable,Usable,HostsRequested,Utilization"]
    for a in allocations:
        rows.append(
            f"{a.name},{a.site},{a.network},{a.prefix_len},{a.mask},"
            f"{a.wildcard},{a.broadcast},{a.gateway},{a.first_usable},"
            f"{a.last_usable},{a.usable_count},{a.hosts_requested},{a.utilization}"
        )
    return "\n".join(rows)


def build_summary_json_data(scenario, decisions: list, allocations: list,
                            media_results: list) -> dict:
    """Build summary.json data."""
    return {
        "profile": scenario.profile,
        "root_prefix": scenario.root_prefix,
        "total_decisions": len(decisions),
        "total_subnets": len(allocations),
        "total_hosts_requested": sum(a.hosts_requested for a in allocations),
        "total_usable_addresses": sum(a.usable_count for a in allocations),
        "efficiency_percent": round(
            sum(a.hosts_requested for a in allocations) /
            max(1, sum(a.usable_count for a in allocations)) * 100, 1
        ),
        "links": [
            {
                "name": f"{m.link_a}-{m.link_b}",
                "distance_m": m.distance_m,
                "media": m.media_type,
                "standard": m.standard,
                "margin_db": m.margin_db,
            }
            for m in media_results
        ],
    }

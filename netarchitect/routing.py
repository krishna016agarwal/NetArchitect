"""
routing.py — Routing protocol selector for NetArchitect.
"""
from netarchitect.models import RoutingConfig, Decision
from netarchitect.constants import (
    OSPF_PROCESS_ID, OSPF_MAX_SUBNETS_SINGLE_AREA,
    ONPREM_ASN, CLOUD_ASN,
)


def select_routing(scenario, allocations: list) -> tuple:
    """Select routing protocol(s) based on scenario profile and topology.

    Returns (RoutingConfig, list[Decision]).
    """
    decisions = []
    num_sites = len(scenario.sites)
    num_subnets = len(allocations)
    has_cloud = bool(scenario.extras.get("cloud_prefix"))
    has_explicit_multi_area = any(s.area not in (None, 0) for s in scenario.sites)

    # Determine protocol
    if (num_sites <= 1 or (num_sites > 1 and not has_explicit_multi_area and scenario.profile in ("campus", "metro") and not has_cloud)):
        # Single area OSPF
        ospf_areas = {s.name: 0 for s in scenario.sites}
        config = RoutingConfig(
            protocol="ospf",
            ospf_areas=ospf_areas,
            is_multi_area=False,
            has_bgp=False,
        )
        decisions.append(Decision(
            rule_id="ROUTE-001",
            domain="routing",
            subject="Protocol selection",
            choice="OSPF single-area (Area 0)",
            reason=(
                f"Selected single-area OSPF (Area 0) because the network has "
                f"{num_sites} site(s) and {num_subnets} subnets, which is below "
                f"the {OSPF_MAX_SUBNETS_SINGLE_AREA}-subnet threshold for "
                f"multi-area partitioning. Link-state routing provides fast "
                f"convergence via SPF computation (RFC 2328)."
            ),
            references=["RFC 2328"],
        ))

    elif num_sites > 1 and has_cloud:
        # Multi-area OSPF + eBGP to cloud
        ospf_areas = {}
        for site in scenario.sites:
            if site.area is not None:
                ospf_areas[site.name] = site.area
            else:
                ospf_areas[site.name] = 0

        # Build area ranges from hierarchical allocations
        area_ranges = {}
        for alloc in allocations:
            if alloc.aggregate_prefix:
                site = alloc.site
                if site in ospf_areas:
                    area = ospf_areas[site]
                    if area not in area_ranges:
                        area_ranges[area] = alloc.aggregate_prefix

        config = RoutingConfig(
            protocol="ospf+bgp",
            ospf_areas=ospf_areas,
            is_multi_area=True,
            has_bgp=True,
            bgp_local_as=ONPREM_ASN,
            bgp_cloud_as=CLOUD_ASN,
            area_ranges=area_ranges,
        )
        decisions.append(Decision(
            rule_id="ROUTE-002",
            domain="routing",
            subject="Protocol selection",
            choice=f"Multi-area OSPF + eBGP (ASN {ONPREM_ASN} <-> {CLOUD_ASN})",
            reason=(
                f"Selected multi-area OSPF because the network spans "
                f"{num_sites} sites with {num_subnets} subnets. Each city "
                f"gets its own OSPF area for LSA containment and "
                f"summarization via area-range on ABRs (RFC 2328). "
                f"eBGP connects on-premises ASN {ONPREM_ASN} to cloud "
                f"ASN {CLOUD_ASN} for external reachability (RFC 4271, "
                f"RFC 6996 private ASNs)."
            ),
            references=["RFC 2328", "RFC 4271", "RFC 6996"],
        ))

    else:
        # Multi-area OSPF without BGP
        ospf_areas = {}
        for site in scenario.sites:
            if site.area is not None:
                ospf_areas[site.name] = site.area
            else:
                ospf_areas[site.name] = 0

        area_ranges = {}
        for alloc in allocations:
            if alloc.aggregate_prefix:
                site = alloc.site
                if site in ospf_areas:
                    area = ospf_areas[site]
                    if area not in area_ranges:
                        area_ranges[area] = alloc.aggregate_prefix

        config = RoutingConfig(
            protocol="ospf",
            ospf_areas=ospf_areas,
            is_multi_area=True,
            has_bgp=False,
            area_ranges=area_ranges,
        )
        decisions.append(Decision(
            rule_id="ROUTE-003",
            domain="routing",
            subject="Protocol selection",
            choice="Multi-area OSPF",
            reason=(
                f"Selected multi-area OSPF because the network spans "
                f"{num_sites} sites with {num_subnets} subnets. Each site "
                f"gets its own OSPF area for scalability (RFC 2328). "
                f"Area 0 serves as the backbone."
            ),
            references=["RFC 2328"],
        ))

    return config, decisions

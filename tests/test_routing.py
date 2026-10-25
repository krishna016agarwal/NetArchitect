"""
test_routing.py — Unit tests for routing protocol selector.
Tests:
  - Single-area OSPF for single-site or < 50 subnets without cloud
  - Multi-area OSPF for multi-site topologies
  - Multi-area OSPF + eBGP to cloud (ASN 65001 -> 65010)
  - Accurate decision justifications and RFC references
"""
import pytest
from netarchitect.models import Scenario, Site, Device, Link, Vlan, SubnetAllocation
from netarchitect.routing import select_routing


def _make_dummy_alloc(name, site="SiteA", network="10.0.0.0", prefix=24):
    return SubnetAllocation(
        name=name, site=site, hosts_requested=50, network=network, prefix_len=prefix,
        mask="255.255.255.0", wildcard="0.0.0.255", broadcast="10.0.0.255",
        gateway="10.0.0.1", first_usable="10.0.0.1", last_usable="10.0.0.254",
        usable_count=254, utilization=19.7,
    )


def test_routing_single_area_ospf():
    """Single site with small subnet count selects single-area OSPF (Area 0)."""
    scenario = Scenario(
        profile="campus", root_prefix="10.10.0.0/16",
        sites=[Site(name="MainCampus", devices=[Device("CORE-1", "l3_switch")])],
        links=[], vlans=[Vlan(10, "Data", 100, "MainCampus")], resiliency=False,
    )
    allocs = [_make_dummy_alloc("Data", "MainCampus")]
    cfg, decs = select_routing(scenario, allocs)

    assert cfg.protocol == "ospf"
    assert cfg.is_multi_area is False
    assert cfg.has_bgp is False
    assert cfg.ospf_areas["MainCampus"] == 0
    assert any("RFC 2328" in ref for d in decs for ref in d.references)


def test_routing_multi_area_ospf_without_cloud():
    """Multi-site scenario without cloud selects multi-area OSPF."""
    scenario = Scenario(
        profile="enterprise", root_prefix="10.10.0.0/16",
        sites=[
            Site(name="Delhi", devices=[Device("R1", "router")], area=0),
            Site(name="Mumbai", devices=[Device("R2", "router")], area=1),
        ],
        links=[Link("Delhi", "Mumbai", 1400000)],
        vlans=[], resiliency=False,
    )
    allocs = [
        _make_dummy_alloc("Delhi-LAN", "Delhi", "10.10.0.0", 24),
        _make_dummy_alloc("Mumbai-LAN", "Mumbai", "10.10.1.0", 24),
    ]
    cfg, decs = select_routing(scenario, allocs)

    assert cfg.is_multi_area is True
    assert cfg.has_bgp is False
    assert cfg.ospf_areas["Delhi"] == 0
    assert cfg.ospf_areas["Mumbai"] == 1


def test_routing_multi_area_ospf_with_bgp_to_cloud():
    """Multi-site with cloud prefix selects multi-area OSPF + eBGP."""
    scenario = Scenario(
        profile="wan", root_prefix="10.100.0.0/16",
        sites=[
            Site(name="Delhi", devices=[Device("RTR-DELHI", "router")], area=0),
            Site(name="Mumbai", devices=[Device("RTR-MUMBAI", "router")], area=1),
        ],
        links=[Link("Delhi", "Mumbai", 1150000)],
        vlans=[], resiliency=False,
        extras={"cloud_prefix": "10.200.0.0/16"},
    )
    allocs = [
        _make_dummy_alloc("Delhi-IoT", "Delhi", "10.100.0.0", 22),
        _make_dummy_alloc("Mumbai-IoT", "Mumbai", "10.100.4.0", 23),
    ]
    cfg, decs = select_routing(scenario, allocs)

    assert cfg.is_multi_area is True
    assert cfg.has_bgp is True
    assert cfg.bgp_local_as == 65001
    assert cfg.bgp_cloud_as == 65010
    assert any("RFC 4271" in ref for d in decs for ref in d.references)
    assert any("RFC 6996" in ref for d in decs for ref in d.references)

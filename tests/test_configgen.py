"""
test_configgen.py — Tests for Cisco IOS config generator.
Validates:
  1. Strict adherence to ios_allowlist.py prefixes for every generated line.
  2. Every SVI IP is strictly inside its allocated subnet.
  3. Every trunk has an explicit allowed VLAN list and native VLAN != 1.
  4. Access ports have PortFast and BPDU Guard enabled.
  5. OSPF network statements use exact inverse wildcard masks matching the interface subnet.
  6. SVIs are configured as passive-interfaces in OSPF.
"""
import re
import ipaddress
import pytest
from netarchitect.inputs import load_preset
from netarchitect.media import select_media
from netarchitect.vlsm import allocate_vlsm, allocate_hierarchical
from netarchitect.routing import select_routing
from netarchitect.configgen import generate_all_configs
from netarchitect.ios_allowlist import is_allowed_ios_line


@pytest.fixture(params=["campus", "metro", "wan"])
def preset_configs(request):
    """Fixture providing generated configs for each built-in preset."""
    scenario = load_preset(request.param)
    media_results = [
        select_media(l.a, l.b, l.distance_m, l.media_request, scenario.profile)[0]
        for l in scenario.links
    ]

    vlan_reqs = [{"name": v.name, "hosts": v.hosts, "site": v.site} for v in scenario.vlans]
    ptp_reqs = [{"name": f"P2P-{l.a}-{l.b}", "hosts": 2, "site": l.a, "is_ptp": True} for l in scenario.links]
    lb_reqs = [{"name": f"Lo0-{d.name}", "hosts": 1, "site": s.name, "is_loopback": True}
               for s in scenario.sites for d in s.devices]

    allow_slash31 = scenario.extras.get("allow_slash31", False)
    if scenario.profile == "wan":
        sites_vlans = {}
        for r in vlan_reqs:
            sites_vlans.setdefault(r["site"], []).append(r)
        allocs, _ = allocate_hierarchical(scenario.root_prefix, sites_vlans, ptp_reqs, lb_reqs, allow_slash31)
    else:
        allocs, _ = allocate_vlsm(scenario.root_prefix, vlan_reqs + ptp_reqs + lb_reqs, allow_slash31)

    routing_cfg, _ = select_routing(scenario, allocs)
    configs, _ = generate_all_configs(scenario, allocs, media_results, routing_cfg)
    return scenario, allocs, configs


def test_ios_allowlist_compliance(preset_configs):
    """Assert every single emitted line in generated configs matches ios_allowlist."""
    scenario, allocs, configs = preset_configs
    for dev_name, config_text in configs.items():
        for line_num, line in enumerate(config_text.splitlines(), start=1):
            assert is_allowed_ios_line(line), (
                f"Preset {scenario.profile}, Device {dev_name}, line {line_num}: "
                f"'{line}' violated ios_allowlist!"
            )


def test_svi_ip_inside_allocated_subnet(preset_configs):
    """Every configured SVI IP must be inside its allocated subnet."""
    scenario, allocs, configs = preset_configs
    alloc_map = {a.name: a for a in allocs}

    for dev_name, config_text in configs.items():
        # Match 'interface Vlan<id>' followed by 'ip address <ip> <mask>'
        svi_matches = re.findall(
            r"interface Vlan(\d+)\s+description (\S+) SVI\s+ip address (\S+) (\S+)",
            config_text
        )
        for vlan_id, vlan_name, ip_str, mask_str in svi_matches:
            alloc = alloc_map.get(vlan_name)
            if alloc:
                oracle_net = ipaddress.IPv4Network(f"{alloc.network}/{alloc.prefix_len}")
                svi_ip = ipaddress.IPv4Address(ip_str)
                assert svi_ip in oracle_net, (
                    f"Device {dev_name}: SVI {vlan_name} ({ip_str}) outside {oracle_net}"
                )


def test_trunk_security_configuration(preset_configs):
    """Verify trunks have explicit allowed VLAN list and native VLAN 999 (not 1)."""
    scenario, allocs, configs = preset_configs
    for dev_name, config_text in configs.items():
        if "switchport mode trunk" in config_text:
            assert "switchport trunk allowed vlan" in config_text, (
                f"Device {dev_name}: trunk missing explicit allowed VLAN list"
            )
            assert "switchport trunk native vlan 999" in config_text, (
                f"Device {dev_name}: trunk not using dedicated native VLAN 999"
            )


def test_access_port_security(preset_configs):
    """Access ports must have spanning-tree portfast and bpduguard enable."""
    scenario, allocs, configs = preset_configs
    for dev_name, config_text in configs.items():
        if "switchport mode access" in config_text:
            assert "spanning-tree portfast" in config_text
            assert "spanning-tree bpduguard enable" in config_text


def test_ospf_wildcard_and_passive_interface(preset_configs):
    """OSPF network statements must have correct wildcard masks and passive LAN interfaces."""
    scenario, allocs, configs = preset_configs
    alloc_by_net = {a.network: a for a in allocs}

    for dev_name, config_text in configs.items():
        if "router ospf" in config_text:
            # Check network statements
            net_matches = re.findall(r"network\s+(\S+)\s+(\S+)\s+area\s+(\d+)", config_text)
            for net_str, wildcard_str, area_id in net_matches:
                alloc = alloc_by_net.get(net_str)
                if alloc:
                    assert wildcard_str == alloc.wildcard, (
                        f"Device {dev_name}: network {net_str} wildcard mismatch. "
                        f"Expected {alloc.wildcard}, got {wildcard_str}"
                    )
            # If SVIs exist, passive-interface must be present
            if "interface Vlan" in config_text:
                assert "passive-interface Vlan" in config_text, (
                    f"Device {dev_name}: SVIs configured but passive-interface missing"
                )

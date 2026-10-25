"""
configgen.py — Cisco IOS configuration generator using Jinja2 templates.
"""
import os
from jinja2 import Environment, FileSystemLoader
from netarchitect.models import (
    Scenario, DeviceConfig, SubnetAllocation, MediaSelection, RoutingConfig, Decision,
)
from netarchitect.constants import (
    NATIVE_VLAN_ID, STP_ROOT_PRIORITY, OSPF_PROCESS_ID,
    ONPREM_ASN, CLOUD_ASN,
    IPSEC_PRESHARED_KEY_PLACEHOLDER, QOS_VOICE_PRIORITY_PERCENT,
)
from netarchitect.vlsm import ip_to_int, int_to_ip, prefix_to_mask_int, mask_to_wildcard_int


def _get_template_env():
    """Get Jinja2 template environment."""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    return Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _find_alloc(allocations, name):
    """Find a subnet allocation by name."""
    for a in allocations:
        if a.name == name:
            return a
    return None


def _find_allocs_for_site(allocations, site_name):
    """Find all non-PTP, non-loopback allocations for a site."""
    return [a for a in allocations if a.site == site_name
            and not a.is_ptp and not a.is_loopback]


def _find_ptp_for_link(allocations, link_a, link_b):
    """Find PTP allocation for a link."""
    for a in allocations:
        if a.is_ptp and (
            a.name == f"P2P-{link_a}-{link_b}" or
            a.name == f"P2P-{link_b}-{link_a}"
        ):
            return a
    return None


def _find_loopback(allocations, device_name):
    """Find loopback allocation for a device."""
    for a in allocations:
        if a.is_loopback and a.name == f"Lo0-{device_name}":
            return a
    return None


def build_device_configs(scenario: Scenario, allocations: list,
                         media_results: list, routing_config: RoutingConfig) -> list:
    """Build DeviceConfig objects for all devices in the scenario.

    Returns list of DeviceConfig.
    """
    device_configs = []
    all_devices = []
    for site in scenario.sites:
        for dev in site.devices:
            all_devices.append((site, dev))

    # Determine which device is the "core" (first in first site) for STP root
    core_device = all_devices[0][1].name if all_devices else ""

    # Build VLAN-to-site mapping
    site_vlans = {}
    for vlan in scenario.vlans:
        site_vlans.setdefault(vlan.site, []).append(vlan)

    # Identify restricted VLANs for ACLs (Students, Labs -> deny to Servers, Mgmt)
    restricted_vlan_names = {"Students", "Labs"}
    protected_vlan_names = {"Servers", "Mgmt", "Management"}

    for site, dev in all_devices:
        is_l3 = dev.device_type in ("l3_switch", "router")
        dc = DeviceConfig(
            hostname=dev.name,
            device_type=dev.device_type,
            supports_isl=dev.supports_isl,
            site_name=site.name,
            ip_routing=is_l3,
            native_vlan=NATIVE_VLAN_ID,
            stp_mode="rapid-pvst",
            stp_is_root=(dev.name == core_device),
            stp_root_priority=STP_ROOT_PRIORITY,
        )

        # VLANs local to this site
        local_vlans = site_vlans.get(site.name, [])
        dc.vlans = [{"id": v.id, "name": v.name} for v in local_vlans]

        # SVIs (one per local VLAN, with gateway from allocation)
        site_allocs = _find_allocs_for_site(allocations, site.name)
        for vlan in local_vlans:
            alloc = None
            for a in site_allocs:
                if a.name == vlan.name:
                    alloc = a
                    break
            if alloc:
                dc.svis.append({
                    "vlan_id": vlan.id,
                    "ip": alloc.gateway,
                    "mask": alloc.mask,
                    "name": vlan.name,
                    "network": alloc.network,
                    "wildcard": alloc.wildcard,
                })

        # Trunk ports to other devices at the same site or inter-site
        vlan_id_list = ",".join(str(v.id) for v in local_vlans) if local_vlans else ""
        trunk_idx = 1
        for link in scenario.links:
            if link.a == site.name or link.b == site.name:
                other = link.b if link.a == site.name else link.a
                # Check if this is a routed link (inter-site between L3 devices)
                ptp_alloc = _find_ptp_for_link(allocations, link.a, link.b)
                if ptp_alloc and is_l3:
                    # Routed port
                    is_a_side = (link.a == site.name)
                    if is_a_side:
                        port_ip = ptp_alloc.gateway
                    else:
                        port_ip = ptp_alloc.last_usable
                    dc.routed_ports.append({
                        "interface": f"GigabitEthernet0/{trunk_idx}",
                        "ip": port_ip,
                        "mask": ptp_alloc.mask,
                        "description": f"P2P to {other}",
                        "network": ptp_alloc.network,
                        "wildcard": ptp_alloc.wildcard,
                    })
                elif vlan_id_list:
                    dc.trunk_ports.append({
                        "interface": f"GigabitEthernet0/{trunk_idx}",
                        "allowed_vlans": vlan_id_list,
                        "native_vlan": NATIVE_VLAN_ID,
                        "needs_encap": dev.supports_isl,
                        "description": f"Trunk to {other}",
                    })
                trunk_idx += 1

        # Access ports
        for vlan in local_vlans:
            dc.access_ports.append({
                "interface": f"GigabitEthernet1/0/{vlan.id % 48 + 1}",
                "vlan": vlan.id,
                "description": f"{vlan.name} access",
            })

        # Loopback
        lo_alloc = _find_loopback(allocations, dev.name)
        if lo_alloc:
            dc.loopbacks.append({
                "interface": "Loopback0",
                "ip": lo_alloc.gateway,
                "mask": lo_alloc.mask,
                "description": f"Router-ID {dev.name}",
            })

        # OSPF configuration
        area = routing_config.ospf_areas.get(site.name, 0)
        ospf_networks = []

        # Add SVI networks
        for svi in dc.svis:
            ospf_networks.append({
                "network": svi["network"],
                "wildcard": svi["wildcard"],
                "area": area,
            })

        # Add routed port networks
        for rp in dc.routed_ports:
            ospf_networks.append({
                "network": rp["network"],
                "wildcard": rp["wildcard"],
                "area": area if not routing_config.is_multi_area else 0,
                # P2P links in area 0 for multi-area (ABR backbone links)
            })

        # Add loopback networks
        for lo in dc.loopbacks:
            ospf_networks.append({
                "network": lo["ip"],
                "wildcard": "0.0.0.0",
                "area": area,
            })

        # Passive interfaces (SVIs are LAN-facing)
        passive_ifaces = [f"Vlan{svi['vlan_id']}" for svi in dc.svis]

        # Area ranges for ABR
        area_ranges_list = []
        if routing_config.is_multi_area and area == 0:
            for ar_area, ar_prefix in routing_config.area_ranges.items():
                if ar_area != 0:
                    ip_s, plen_s = ar_prefix.split("/")
                    plen = int(plen_s)
                    mask_int = prefix_to_mask_int(plen)
                    area_ranges_list.append({
                        "area": ar_area,
                        "network": ip_s,
                        "mask": int_to_ip(mask_int),
                    })

        router_id = lo_alloc.gateway if lo_alloc else (
            dc.svis[0]["ip"] if dc.svis else "1.1.1.1"
        )

        dc.ospf = {
            "process_id": OSPF_PROCESS_ID,
            "router_id": router_id,
            "networks": ospf_networks,
            "passive_interfaces": passive_ifaces,
            "area_ranges": area_ranges_list,
        }

        # ACLs (campus profile)
        if scenario.profile == "campus":
            # Find protected subnets
            protected_subnets = []
            for a in allocations:
                if a.name in protected_vlan_names:
                    protected_subnets.append(a)

            for vlan in local_vlans:
                if vlan.name in restricted_vlan_names:
                    acl_name = f"RESTRICT-{vlan.name.upper()}"
                    entries = []
                    for ps in protected_subnets:
                        entries.append(
                            f"remark Deny {vlan.name} to {ps.name}"
                        )
                        entries.append(
                            f"deny ip any {ps.network} {ps.wildcard}"
                        )
                    entries.append("remark Allow all other traffic")
                    entries.append("permit ip any any")

                    dc.acls.append({
                        "name": acl_name,
                        "entries": entries,
                    })
                    dc.acl_applications.append({
                        "interface": f"Vlan{vlan.id}",
                        "acl_name": acl_name,
                        "direction": "in",
                    })

        # BGP (WAN profile with cloud)
        if routing_config.has_bgp and site.name == scenario.sites[0].name:
            cloud_prefix = scenario.extras.get("cloud_prefix", "")
            if cloud_prefix:
                cp_ip, cp_plen = cloud_prefix.split("/")
                cp_mask_int = prefix_to_mask_int(int(cp_plen))
                dc.bgp = {
                    "local_as": routing_config.bgp_local_as,
                    "neighbors": [
                        {
                            "ip": "10.200.0.1",  # placeholder cloud peer
                            "remote_as": routing_config.bgp_cloud_as,
                        }
                    ],
                    "networks": [
                        {
                            "network": scenario.root_prefix.split("/")[0],
                            "mask": int_to_ip(prefix_to_mask_int(
                                int(scenario.root_prefix.split("/")[1]))),
                        }
                    ],
                }

        # IPsec (WAN profile)
        if scenario.profile == "wan" and routing_config.has_bgp and site.name == scenario.sites[0].name:
            cloud_prefix = scenario.extras.get("cloud_prefix", "")
            if cloud_prefix:
                cp_ip, cp_plen = cloud_prefix.split("/")
                cp_mask_int = prefix_to_mask_int(int(cp_plen))
                cp_wildcard = mask_to_wildcard_int(cp_mask_int)
                root_ip, root_plen = scenario.root_prefix.split("/")
                root_mask_int = prefix_to_mask_int(int(root_plen))
                root_wildcard = mask_to_wildcard_int(root_mask_int)
                dc.ipsec = {
                    "preshared_key": IPSEC_PRESHARED_KEY_PLACEHOLDER,
                    "peer_ip": "10.200.0.1",
                    "acl_name": "IPSEC-INTERESTING",
                    "local_network": root_ip,
                    "local_wildcard": int_to_ip(root_wildcard),
                    "remote_network": cp_ip,
                    "remote_wildcard": int_to_ip(cp_wildcard),
                    "map_name": "IPSEC-MAP",
                    "interface": dc.routed_ports[0]["interface"] if dc.routed_ports else "GigabitEthernet0/0",
                }

        # QoS (metro profile)
        if scenario.profile == "metro":
            if dc.routed_ports:
                dc.qos = {
                    "priority_percent": QOS_VOICE_PRIORITY_PERCENT,
                    "interface": dc.routed_ports[0]["interface"],
                }

        # Subinterfaces (metro EVPL handoff)
        if scenario.profile == "metro" and dc.routed_ports:
            for vlan in local_vlans:
                alloc = None
                for a in site_allocs:
                    if a.name == vlan.name:
                        alloc = a
                        break
                if alloc:
                    base_iface = dc.routed_ports[0]["interface"]
                    dc.subinterfaces.append({
                        "interface": f"{base_iface}.{vlan.id}",
                        "encapsulation": f"dot1Q {vlan.id}",
                        "ip": alloc.gateway,
                        "mask": alloc.mask,
                        "description": f"EVPL {vlan.name}",
                    })

        device_configs.append(dc)

    return device_configs


def render_device_config(dc: DeviceConfig) -> str:
    """Render a single device config using Jinja2 template."""
    env = _get_template_env()
    template = env.get_template("device.j2")
    return template.render(
        hostname=dc.hostname,
        device_type=dc.device_type,
        supports_isl=dc.supports_isl,
        ip_routing=dc.ip_routing,
        vlans=dc.vlans,
        native_vlan=dc.native_vlan,
        stp_mode=dc.stp_mode,
        stp_is_root=dc.stp_is_root,
        stp_root_priority=dc.stp_root_priority,
        svis=dc.svis,
        trunk_ports=dc.trunk_ports,
        access_ports=dc.access_ports,
        routed_ports=dc.routed_ports,
        loopbacks=dc.loopbacks,
        subinterfaces=dc.subinterfaces,
        ospf=dc.ospf,
        bgp=dc.bgp,
        acls=dc.acls,
        acl_applications=dc.acl_applications,
        ipsec=dc.ipsec,
        qos=dc.qos,
    )


def generate_all_configs(scenario, allocations, media_results, routing_config):
    """Generate configs for all devices.

    Returns dict {device_name: config_text} and list[Decision].
    """
    decisions = []
    device_configs = build_device_configs(scenario, allocations, media_results, routing_config)
    configs = {}
    for dc in device_configs:
        config_text = render_device_config(dc)
        configs[dc.hostname] = config_text
        decisions.append(Decision(
            rule_id=f"CONFIG-{dc.hostname}",
            domain="security",
            subject=f"Device {dc.hostname}",
            choice=f"Generated IOS config ({len(config_text.splitlines())} lines)",
            reason=(
                f"Configuration for {dc.hostname} ({dc.device_type}) at site "
                f"{dc.site_name}: {len(dc.svis)} SVIs, {len(dc.trunk_ports)} trunks, "
                f"{len(dc.routed_ports)} routed ports, "
                f"{'OSPF' if dc.ospf else 'no routing'}"
                f"{', BGP' if dc.bgp else ''}"
                f"{', IPsec' if dc.ipsec else ''}"
                f"{', QoS' if dc.qos else ''}."
            ),
            references=["IEEE 802.1Q", "IEEE 802.1w"],
        ))
    return configs, decisions

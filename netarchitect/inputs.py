"""
inputs.py — JSON loader with validation for NetArchitect.
"""
import json
import os
from netarchitect.models import Scenario, Site, Device, Link, Vlan
from netarchitect.errors import InvalidParameterError
from netarchitect.constants import VLAN_MIN, VLAN_MAX, VLAN_RESERVED_START, VLAN_RESERVED_END


def _parse_ip_prefix(prefix_str: str) -> tuple:
    """Parse and validate an IP/prefix string. Returns (ip_str, prefix_len)."""
    try:
        ip_str, plen_str = prefix_str.split("/")
        prefix_len = int(plen_str)
    except (ValueError, AttributeError):
        raise InvalidParameterError(
            f"Invalid prefix format '{prefix_str}': expected 'A.B.C.D/N'"
        )
    if prefix_len < 0 or prefix_len > 32:
        raise InvalidParameterError(
            f"Prefix length {prefix_len} out of range [0, 32]"
        )
    parts = ip_str.split(".")
    if len(parts) != 4:
        raise InvalidParameterError(f"Invalid IP address '{ip_str}'")
    for p in parts:
        try:
            v = int(p)
        except ValueError:
            raise InvalidParameterError(f"Invalid octet '{p}' in IP '{ip_str}'")
        if v < 0 or v > 255:
            raise InvalidParameterError(f"Octet {v} out of range in IP '{ip_str}'")
    return ip_str, prefix_len


def _is_rfc1918(ip_str: str) -> bool:
    """Check if an IP is in RFC 1918 private address space."""
    parts = list(map(int, ip_str.split(".")))
    ip_int = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
    # 10.0.0.0/8
    if (ip_int >> 24) == 10:
        return True
    # 172.16.0.0/12
    if (ip_int >> 20) == (172 << 4 | 1):  # 0xAC1 = 2753
        return True
    # 192.168.0.0/16
    if (ip_int >> 16) == (192 << 8 | 168):
        return True
    return False


def validate_scenario(scenario: Scenario):
    """Validate a parsed Scenario object."""
    # Validate root prefix
    ip_str, _ = _parse_ip_prefix(scenario.root_prefix)
    if not _is_rfc1918(ip_str):
        raise InvalidParameterError(
            f"Root prefix {scenario.root_prefix} is not RFC 1918 private space"
        )

    # Validate links
    for link in scenario.links:
        if link.distance_m <= 0:
            raise InvalidParameterError(
                f"Link {link.a}-{link.b}: distance must be > 0, got {link.distance_m}"
            )

    # Validate VLANs
    seen_ids = set()
    for vlan in scenario.vlans:
        if vlan.hosts < 1:
            raise InvalidParameterError(
                f"VLAN {vlan.id} '{vlan.name}': hosts must be >= 1, got {vlan.hosts}"
            )
        if vlan.id < VLAN_MIN or vlan.id > VLAN_MAX:
            raise InvalidParameterError(
                f"VLAN {vlan.id}: ID out of range [{VLAN_MIN}, {VLAN_MAX}]"
            )
        if VLAN_RESERVED_START <= vlan.id <= VLAN_RESERVED_END:
            raise InvalidParameterError(
                f"VLAN {vlan.id}: reserved range {VLAN_RESERVED_START}-{VLAN_RESERVED_END}"
            )
        if vlan.id in seen_ids:
            raise InvalidParameterError(
                f"VLAN {vlan.id}: duplicate ID"
            )
        seen_ids.add(vlan.id)

    # Validate sites
    site_names = {s.name for s in scenario.sites}
    if len(site_names) != len(scenario.sites):
        raise InvalidParameterError("Duplicate site names detected")

    # Resiliency check: at least 2 disjoint paths to every site
    if scenario.resiliency:
        for site in scenario.sites:
            connections = sum(
                1 for link in scenario.links
                if link.a == site.name or link.b == site.name
            )
            if connections < 2 and len(scenario.sites) > 1:
                raise InvalidParameterError(
                    f"Resiliency requires at least 2 disjoint paths to site "
                    f"'{site.name}', but it has only {connections} link(s)"
                )


def load_json(path: str) -> Scenario:
    """Load a scenario from a JSON file with validation."""
    if not os.path.isfile(path):
        raise InvalidParameterError(f"File not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise InvalidParameterError(f"JSON parse error at line {e.lineno}: {e.msg}")

    # Required keys
    for key in ("profile", "root_prefix", "sites", "links", "vlans"):
        if key not in data:
            raise InvalidParameterError(f"Missing required key '{key}' in JSON")

    # Build sites
    sites = []
    for s in data["sites"]:
        devices = [
            Device(
                name=d["name"],
                device_type=d.get("type", "l3_switch"),
                supports_isl=d.get("supports_isl", False),
            )
            for d in s.get("devices", [])
        ]
        sites.append(Site(
            name=s["name"],
            devices=devices,
            area=s.get("area"),
        ))

    # Build links
    links = [
        Link(
            a=lk["a"],
            b=lk["b"],
            distance_m=float(lk["distance_m"]),
            media_request=lk.get("media_request"),
        )
        for lk in data["links"]
    ]

    # Build VLANs
    vlans = [
        Vlan(
            id=v["id"],
            name=v["name"],
            hosts=int(v["hosts"]),
            site=v["site"],
            poe=v.get("poe", False),
        )
        for v in data["vlans"]
    ]

    scenario = Scenario(
        profile=data["profile"],
        root_prefix=data["root_prefix"],
        sites=sites,
        links=links,
        vlans=vlans,
        resiliency=data.get("resiliency", False),
        extras=data.get("extras", {}),
    )

    validate_scenario(scenario)
    return scenario


def load_preset(preset_name: str) -> Scenario:
    """Load a built-in preset by name."""
    presets_dir = os.path.join(os.path.dirname(__file__), "presets")
    path = os.path.join(presets_dir, f"{preset_name}.json")
    if not os.path.isfile(path):
        raise InvalidParameterError(
            f"Unknown preset '{preset_name}'. Available: campus, metro, wan"
        )
    return load_json(path)

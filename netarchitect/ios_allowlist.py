"""
ios_allowlist.py — Allowed Cisco IOS command prefixes.

Every emitted config line (after stripping leading whitespace) must start
with one of these prefixes. A test asserts this for all generated configs.
Blank lines and comment lines starting with '!' are always allowed.
"""

IOS_COMMAND_PREFIXES = [
    # Global configuration
    "hostname ",
    "no ip domain-lookup",
    "no ip domain lookup",
    "ip routing",

    # VLAN
    "vlan ",
    "name ",

    # Spanning Tree — IEEE 802.1w
    "spanning-tree ",

    # Interface configuration
    "interface ",
    "description ",
    "ip address ",
    "no switchport",
    "no shutdown",
    "shutdown",
    "switchport ",
    "encapsulation ",

    # OSPF — RFC 2328
    "router ospf",
    "router-id ",
    "network ",
    "passive-interface ",
    "area ",

    # BGP — RFC 4271
    "router bgp ",
    "neighbor ",
    "address-family ",

    # ACLs
    "ip access-list ",
    "permit ",
    "deny ",
    "remark ",
    "ip access-group ",

    # IPsec — RFC 4301
    "crypto ",

    # QoS
    "class-map ",
    "match ",
    "policy-map ",
    "class ",
    "priority ",
    "service-policy ",

    # Crypto sub-commands
    "encr ",
    "authentication ",
    "group ",
    "hash ",
    "set ",
    "mode ",

    # Static routes
    "ip route ",

    # Control
    "exit",
    "end",
]


def is_allowed_ios_line(line: str) -> bool:
    """Check if a config line is allowed by the IOS allowlist.

    Blank lines and '!' comment lines are always allowed.
    Other lines are stripped of leading whitespace and checked against prefixes.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("!"):
        return True
    return any(stripped.startswith(prefix) for prefix in IOS_COMMAND_PREFIXES)

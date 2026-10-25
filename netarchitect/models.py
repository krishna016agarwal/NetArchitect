"""
models.py — Dataclasses for NetArchitect.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Decision:
    """An explainable design decision with justification."""
    rule_id: str           # e.g. "MEDIA-001", "VLSM-003"
    domain: str            # 'media', 'vlsm', 'routing', 'security', 'qos'
    subject: str           # what this decision is about
    choice: str            # what was chosen
    reason: str            # natural-language justification with computed values
    references: list       # RFC/IEEE references


@dataclass
class Device:
    """A network device (switch or router)."""
    name: str
    device_type: str       # 'l3_switch', 'router', 'access_switch'
    supports_isl: bool = False


@dataclass
class Site:
    """A physical location containing devices."""
    name: str
    devices: list = field(default_factory=list)  # List[Device]
    area: Optional[int] = None  # OSPF area number


@dataclass
class Link:
    """A physical link between two sites."""
    a: str                   # site/device name
    b: str                   # site/device name
    distance_m: float        # distance in metres
    media_request: Optional[str] = None  # 'copper', 'fiber', or None (auto)


@dataclass
class Vlan:
    """A VLAN with host count."""
    id: int
    name: str
    hosts: int
    site: str
    poe: bool = False


@dataclass
class Scenario:
    """Complete network scenario from preset or custom JSON."""
    profile: str             # 'campus', 'metro', 'wan'
    root_prefix: str         # e.g. "10.10.0.0/16"
    sites: list              # List[Site]
    links: list              # List[Link]
    vlans: list              # List[Vlan]
    resiliency: bool
    extras: dict = field(default_factory=dict)
    # extras may contain: cloud_prefix, allow_slash31, etc.


@dataclass
class MediaSelection:
    """Result of L1 media engine for a link."""
    link_a: str
    link_b: str
    distance_m: float
    media_type: str          # 'Cat6a UTP', 'OM4 MMF', 'OS2 SMF'
    standard: str            # '10GBASE-T', '10GBASE-SR', '10GBASE-LR', etc.
    transceiver: Optional[str] = None  # 'LR', 'ER', 'ZR' or None
    wavelength_nm: Optional[int] = None
    budget_db: Optional[float] = None
    loss_db: Optional[float] = None
    margin_db: Optional[float] = None
    propagation_delay_us: float = 0.0
    wan_circuit: bool = False  # True if > 80 km


@dataclass
class SubnetAllocation:
    """Result of VLSM allocation for a single subnet."""
    name: str
    site: str
    hosts_requested: int
    network: str             # dotted-quad
    prefix_len: int
    mask: str                # dotted-quad
    wildcard: str            # dotted-quad
    broadcast: str           # dotted-quad
    gateway: str             # first usable (or network for /31, /32)
    first_usable: str
    last_usable: str
    usable_count: int
    utilization: float       # hosts_requested / usable_count * 100
    is_ptp: bool = False
    is_loopback: bool = False
    aggregate_prefix: Optional[str] = None  # for hierarchical mode


@dataclass
class RoutingConfig:
    """Routing protocol configuration per device."""
    protocol: str            # 'ospf', 'ospf+bgp'
    ospf_areas: dict = field(default_factory=dict)  # site -> area number
    is_multi_area: bool = False
    has_bgp: bool = False
    bgp_local_as: int = 0
    bgp_cloud_as: int = 0
    bgp_peer_ip: str = ""
    area_ranges: dict = field(default_factory=dict)  # area -> (network, mask)


@dataclass
class DeviceConfig:
    """Complete configuration context for a single device."""
    hostname: str
    device_type: str
    supports_isl: bool = False
    site_name: str = ""
    ip_routing: bool = False
    vlans: list = field(default_factory=list)
    native_vlan: int = 999
    stp_mode: str = "rapid-pvst"
    stp_is_root: bool = False
    stp_root_priority: int = 4096
    svis: list = field(default_factory=list)
    trunk_ports: list = field(default_factory=list)
    access_ports: list = field(default_factory=list)
    routed_ports: list = field(default_factory=list)
    loopbacks: list = field(default_factory=list)
    subinterfaces: list = field(default_factory=list)
    ospf: Optional[dict] = None
    bgp: Optional[dict] = None
    acls: list = field(default_factory=list)
    acl_applications: list = field(default_factory=list)
    ipsec: Optional[dict] = None
    qos: Optional[dict] = None

"""
constants.py — All numeric constants for NetArchitect.
Every constant is annotated with the standard or source it comes from.
"""

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1 — DISTANCE THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════

# Maximum distance for Cat6a copper cabling at 10 Gbps
COPPER_MAX_DISTANCE_M = 100  # IEEE 802.3an (10GBASE-T), 100 m channel limit

# Maximum distance for OM4 multimode fiber at 10 Gbps
MMF_OM4_MAX_DISTANCE_M = 400  # IEEE 802.3ae (10GBASE-SR over OM4), 400 m

# Beyond this distance, recommend carrier WAN circuit instead of owned fiber
MAX_OWNED_FIBER_KM = 80  # typical vendor value, configurable


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1 — OPTICAL PARAMETERS
# ═══════════════════════════════════════════════════════════════════════════

# Fiber attenuation coefficients for OS2 single-mode fiber
ATTENUATION_1310_DB_PER_KM = 0.35  # ITU-T G.652 OS2 SMF at 1310 nm
ATTENUATION_1550_DB_PER_KM = 0.25  # ITU-T G.652 OS2 SMF at 1550 nm

# Connector loss per connector
CONNECTOR_LOSS_DB = 0.5  # typical vendor value, configurable
NUM_CONNECTORS = 4       # 2 per end = 4 total, typical vendor value, configurable

# Splice loss per splice point
SPLICE_LOSS_DB = 0.1     # typical vendor value, configurable
# Number of splices = floor(distance_km / 2)

# Safety margin for optical power budget
SAFETY_MARGIN_DB = 2.0   # typical vendor value, configurable

# Propagation delay in fiber
PROPAGATION_DELAY_US_PER_KM = 5  # ~5 µs/km in glass fiber, typical vendor value


# Transceiver specifications: {name: (wavelength_nm, reach_km, tx_min_dBm, rx_sens_dBm, standard)}
TRANSCEIVERS = {
    "LR": {
        "wavelength_nm": 1310,
        "reach_km": 10,
        "tx_min_dbm": -8.2,
        "rx_sens_dbm": -14.4,
        "standard": "IEEE 802.3ae",
        "description": "10GBASE-LR",
    },
    "ER": {
        "wavelength_nm": 1550,
        "reach_km": 40,
        "tx_min_dbm": -4.7,
        "rx_sens_dbm": -15.8,
        "standard": "IEEE 802.3ae",
        "description": "10GBASE-ER",
    },
    "ZR": {
        "wavelength_nm": 1550,
        "reach_km": 80,
        "tx_min_dbm": 0.0,
        "rx_sens_dbm": -24.0,
        "standard": "vendor-specific typical",
        "description": "10GBASE-ZR",
    },
}

# Transceiver cost ranking (lower index = cheaper) for tie-breaking
TRANSCEIVER_COST_ORDER = ["LR", "ER", "ZR"]


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2 — VLAN / STP
# ═══════════════════════════════════════════════════════════════════════════

VLAN_MIN = 1      # IEEE 802.1Q minimum VLAN ID
VLAN_MAX = 4094   # IEEE 802.1Q maximum VLAN ID
VLAN_RESERVED_START = 1002  # FDDI/Token Ring reserved range start
VLAN_RESERVED_END = 1005    # FDDI/Token Ring reserved range end

NATIVE_VLAN_ID = 999  # unused VLAN for native, typical vendor value, configurable
STP_ROOT_PRIORITY = 4096  # IEEE 802.1w, lowest configurable priority for root bridge


# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3 — ROUTING PROTOCOLS
# ═══════════════════════════════════════════════════════════════════════════

OSPF_PROCESS_ID = 1       # typical vendor value, configurable
OSPF_MAX_SUBNETS_SINGLE_AREA = 50  # typical vendor value, configurable; above this → multi-area

ONPREM_ASN = 65001   # RFC 6996 private ASN for on-premises
CLOUD_ASN = 65010    # RFC 6996 private ASN for cloud provider


# ═══════════════════════════════════════════════════════════════════════════
# QoS — METRO PROFILE
# ═══════════════════════════════════════════════════════════════════════════

METRO_MAX_ONE_WAY_DELAY_MS = 5   # typical vendor value, configurable
EQUIPMENT_DELAY_ALLOWANCE_MS = 1  # typical vendor value, configurable
QOS_VOICE_PRIORITY_PERCENT = 30   # typical vendor value, configurable


# ═══════════════════════════════════════════════════════════════════════════
# IPSEC — WAN PROFILE
# ═══════════════════════════════════════════════════════════════════════════

IPSEC_ISAKMP_POLICY_NUM = 10        # typical vendor value, configurable
IPSEC_ENCRYPTION = "aes 256"        # RFC 4301, strong encryption
IPSEC_AUTH_METHOD = "pre-share"     # typical vendor value, configurable
IPSEC_DH_GROUP = 14                 # RFC 3526 MODP 2048-bit, typical vendor value
IPSEC_TRANSFORM_SET_NAME = "IPSEC-TS"  # typical vendor value, configurable
IPSEC_PRESHARED_KEY_PLACEHOLDER = "CHANGE_ME_BEFORE_DEPLOYMENT"  # placeholder

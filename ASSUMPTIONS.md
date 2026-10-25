# NetArchitect — Architectural Assumptions & Standards References

This document records all engineering assumptions, design choices, and standard references used in **NetArchitect** for course **CIC-307** (Computer Networks mini-project).

---

## 1. Allowed Standards & RFC References

Only official, recognized networking standards and RFCs are cited throughout the engines and rationale outputs:

| Standard / RFC | Title / Scope | Application in NetArchitect |
|---|---|---|
| **IEEE 802.3an** | 10GBASE-T (10 Gbps over unshielded/shielded twisted-pair copper) | Enforces the strict 100 m physical channel limit for Cat6a copper cabling. |
| **IEEE 802.3ae** | 10GBASE-SR / LR / ER (10 Gbps over optical fiber) | Specifies OM4 MMF reach (400 m at 850 nm) and OS2 SMF reaches (10 km LR, 40 km ER). |
| **IEEE 802.1Q** | Virtual Bridged Local Area Networks | Standard VLAN encapsulation, trunking, and isolation of Native VLAN 999. |
| **IEEE 802.1w** | Rapid Spanning Tree Protocol (RSTP) | Standardized fast convergence STP mode (`rapid-pvst`) and root priority calculations. |
| **RFC 1918** | Address Allocation for Private Internets | Validates that all root address spaces belong to `10.0.0.0/8`, `172.16.0.0/12`, or `192.168.0.0/16`. |
| **RFC 2328** | OSPF Version 2 | Link-state intra-domain routing protocol, single-area Area 0 and multi-area hierarchies. |
| **RFC 3021** | Using 31-Bit Prefixes on IPv4 Point-to-Point Links | Conserves IP space on point-to-point links by eliminating network/broadcast address overhead. |
| **RFC 4271** | Border Gateway Protocol 4 (BGP-4) | Inter-autonomous system routing connecting on-premises sites to cloud networks. |
| **RFC 4301** | Security Architecture for the Internet Protocol (IPsec) | Securing inter-site transit over untrusted carrier networks and public WANs. |
| **RFC 4632** | Classless Inter-domain Routing (CIDR) | Bitwise hierarchical supernet summarization on Area Border Routers (ABRs). |
| **RFC 6996** | Autonomous System Numbers for Private Use | Designates private Autonomous System numbers: On-Premise ASN 65001 and Cloud ASN 65010. |

---

## 2. Layer 1 Media Engine Assumptions

1. **Copper Cabling Limit**:
   - Cat6a UTP channel length is strictly bounded at 100 m per IEEE 802.3an. Any request for copper media exceeding 100 m raises `PhysicalDistanceViolationError` explaining high-frequency attenuation and alien crosstalk degradation.
2. **Multimode Fiber (MMF)**:
   - OM4 multimode fiber at 850 nm (10GBASE-SR) is selected for links between 101 m and 400 m. Beyond 400 m, modal dispersion limits bandwidth-distance product, requiring single-mode fiber (OS2).
3. **Single-Mode Fiber (OS2) & Transceiver Selection**:
   - Supported transceivers:
     - **LR** (1310 nm, reach 10 km, Tx_min -8.2 dBm, Rx_sens -14.4 dBm)
     - **ER** (1550 nm, reach 40 km, Tx_min -4.7 dBm, Rx_sens -15.8 dBm)
     - **ZR** (1550 nm, reach 80 km, Tx_min 0.0 dBm, Rx_sens -24.0 dBm, vendor-specific typical)
   - Transceiver selection chooses the lowest-cost transceiver meeting both $\text{reach} \ge \text{distance}$ and $\text{optical margin} \ge 0\text{ dB}$.
   - Optical budget formula:
     $$\text{Budget} = \text{Tx}_{\min} - \text{Rx}_{\text{sens}}$$
     $$\text{Total Loss} = (\text{distance}_{\text{km}} \times \alpha) + (4 \times 0.5\text{ dB}) + (\lfloor\text{distance}_{\text{km}} / 2\rfloor \times 0.1\text{ dB}) + 2.0\text{ dB}$$
     $$\text{Margin} = \text{Budget} - \text{Total Loss}$$
     where $\alpha = 0.35\text{ dB/km}$ at 1310 nm and $0.25\text{ dB/km}$ at 1550 nm.
4. **Owned Fiber Distance Limit**:
   - The maximum distance for enterprise-owned fiber is capped at 80 km. Links exceeding 80 km recommend a carrier WAN circuit secured with IPsec.
5. **Propagation Delay**:
   - Assumed propagation speed in glass fiber is $5\ \mu\text{s/km}$. Metro SLA validation requires one-way delay $+ 1\text{ ms}$ equipment processing delay to be $< 5\text{ ms}$.

---

## 3. Layer 3 VLSM Subnet Math Assumptions

1. **Pure Bitwise Integer Operations**:
   - Subnet masks, wildcards, block sizes, alignments, and broadcast addresses are calculated exclusively with integer bit operations (`<<`, `>>`, `&`, `|`, `^`, `~ & 0xFFFFFFFF`). Python's `ipaddress` module is strictly banned from the engine and used solely in automated tests as an independent verification oracle.
2. **Descending Block Allocation**:
   - Allocations are sorted in descending order of block size with a stable tie-break by name. This guarantees zero fragmentation of CIDR address blocks.
3. **Alignment**:
   - Each subnet is aligned to its own power-of-two block boundary using:
     $$\text{cursor} = (\text{cursor} + \text{size} - 1)\ \& \ \sim(\text{size} - 1)\ \& \ \text{0xFFFFFFFF}$$
4. **Usable IP Allocations**:
   - Default subnets: Usable hosts $= \text{block} - 2$.
   - RFC 3021 Point-to-Point links (`/31`): Usable hosts $= 2$ (no dedicated network/broadcast addresses).
   - Loopback interfaces (`/32`): Usable hosts $= 1$.
5. **Default Gateway Convention**:
   - The first usable IP address in every allocated subnet is assigned as the default gateway (SVI / router interface).

---

## 4. Cisco IOS Command Allowlist & Security Assumptions

1. **Strict Command Allowlist**:
   - Every generated configuration line must begin with an approved prefix from `netarchitect/ios_allowlist.py` or be an allowed comment/blank line.
2. **VLAN Security**:
   - Default VLAN 1 is never used for data traffic.
   - An unused, isolated VLAN 999 (`NATIVE`) is configured on all trunk ports to prevent double-tagging 802.1Q VLAN hopping attacks.
   - All trunk links explicitly specify `switchport trunk allowed vlan <explicit_list>` to prevent broadcast leaking.
3. **Spanning Tree Protocol (STP)**:
   - Operating mode is Rapid PVST+ (`spanning-tree mode rapid-pvst`).
   - Core switches are configured with `spanning-tree vlan <id> priority 4096` to guarantee root bridge placement.
   - Access ports enable both `spanning-tree portfast` and `spanning-tree bpduguard enable` to prevent rogue root attacks.
4. **OSPF Routing**:
   - Router IDs are derived deterministically from dedicated `Loopback0` interfaces.
   - All client-facing SVIs and LAN interfaces are configured with `passive-interface` to isolate routing control plane traffic from end hosts.
5. **IPsec & BGP VPN**:
   - Preshared keys use obvious administrative placeholders (`VPN_SECRET_KEY_PLACEHOLDER_CHANGE_IN_PRODUCTION`).
   - Interesting traffic ACLs permit only specified on-premises root supernets to cloud VPC ranges.

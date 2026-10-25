# NetArchitect Design Rationale

## Summary Table

| # | Domain | Subject | Choice | References |
|---|--------|---------|--------|------------|
| 1 | media | Link HQ-R1 (15000.0 m) | OS2 SMF, 10GBASE-ER | IEEE 802.3ae |
| 2 | qos | Link HQ-R1 delay | PASS: 1.07 ms | IEEE 802.3ae |
| 3 | media | Link HQ-R2 (35000.0 m) | OS2 SMF, 10GBASE-ZR | vendor-specific typical |
| 4 | qos | Link HQ-R2 delay | PASS: 1.18 ms | IEEE 802.3ae |
| 5 | media | Link R1-R2 (28000.0 m) | OS2 SMF, 10GBASE-ZR | vendor-specific typical |
| 6 | qos | Link R1-R2 delay | PASS: 1.14 ms | IEEE 802.3ae |
| 7 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 8 | vlsm | HQ-Users (HQ) | 172.16.0.0/24 | RFC 4632 |
| 9 | vlsm | Colo-Servers (HQ) | 172.16.1.0/25 | RFC 4632 |
| 10 | vlsm | R1-Users (R1) | 172.16.1.128/25 | RFC 4632 |
| 11 | vlsm | R2-Users (R2) | 172.16.2.0/25 | RFC 4632 |
| 12 | vlsm | P2P-HQ-R1 (HQ) | 172.16.2.128/30 | RFC 4632 |
| 13 | vlsm | P2P-HQ-R2 (HQ) | 172.16.2.132/30 | RFC 4632 |
| 14 | vlsm | P2P-R1-R2 (R1) | 172.16.2.136/30 | RFC 4632 |
| 15 | vlsm | Lo0-RTR-HQ (HQ) | 172.16.2.140/32 | RFC 4632 |
| 16 | vlsm | Lo0-RTR-R1 (R1) | 172.16.2.141/32 | RFC 4632 |
| 17 | vlsm | Lo0-RTR-R2 (R2) | 172.16.2.142/32 | RFC 4632 |
| 18 | vlsm | Allocation summary | 10 subnets, 87.2% efficient | RFC 4632 |
| 19 | routing | Protocol selection | OSPF single-area (Area 0) | RFC 2328 |
| 20 | security | Device RTR-HQ | Generated IOS config (104 lines) | IEEE 802.1Q, IEEE 802.1w |
| 21 | security | Device RTR-R1 | Generated IOS config (79 lines) | IEEE 802.1Q, IEEE 802.1w |
| 22 | security | Device RTR-R2 | Generated IOS config (79 lines) | IEEE 802.1Q, IEEE 802.1w |

## MEDIA Decisions

### [MEDIA-003] Link HQ-R1 (15000.0 m)

**Choice:** OS2 SMF, 10GBASE-ER

**Reason:** Selected OS2 Single-Mode Fiber (10GBASE-ER) because link HQ-R1 distance (15000.0 m = 15.0 km) exceeds the 400 m limit of OM4 MMF. Optical budget: 11.1 dB (Tx_min -4.7 dBm - Rx_sens -15.8 dBm). Total loss: 8.45 dB (fiber 3.75 + connectors 2.0 + splices 0.7 + safety 2.0). Margin: 2.65 dB.

**References:** IEEE 802.3ae


### [MEDIA-003] Link HQ-R2 (35000.0 m)

**Choice:** OS2 SMF, 10GBASE-ZR

**Reason:** Selected OS2 Single-Mode Fiber (10GBASE-ZR) because link HQ-R2 distance (35000.0 m = 35.0 km) exceeds the 400 m limit of OM4 MMF. Optical budget: 24.0 dB (Tx_min 0.0 dBm - Rx_sens -24.0 dBm). Total loss: 14.45 dB (fiber 8.75 + connectors 2.0 + splices 1.7 + safety 2.0). Margin: 9.55 dB.

**References:** vendor-specific typical


### [MEDIA-003] Link R1-R2 (28000.0 m)

**Choice:** OS2 SMF, 10GBASE-ZR

**Reason:** Selected OS2 Single-Mode Fiber (10GBASE-ZR) because link R1-R2 distance (28000.0 m = 28.0 km) exceeds the 400 m limit of OM4 MMF. Optical budget: 24.0 dB (Tx_min 0.0 dBm - Rx_sens -24.0 dBm). Total loss: 12.4 dB (fiber 7.0 + connectors 2.0 + splices 1.4 + safety 2.0). Margin: 11.6 dB.

**References:** vendor-specific typical


## QOS Decisions

### [MEDIA-004] Link HQ-R1 delay

**Choice:** PASS: 1.07 ms

**Reason:** One-way delay for link HQ-R1: propagation 75.0 µs (15.0 km x 5 µs/km) = 0.07 ms + 1 ms equipment allowance = 1.07 ms. Target < 5 ms: MET.

**References:** IEEE 802.3ae


### [MEDIA-004] Link HQ-R2 delay

**Choice:** PASS: 1.18 ms

**Reason:** One-way delay for link HQ-R2: propagation 175.0 µs (35.0 km x 5 µs/km) = 0.17 ms + 1 ms equipment allowance = 1.18 ms. Target < 5 ms: MET.

**References:** IEEE 802.3ae


### [MEDIA-004] Link R1-R2 delay

**Choice:** PASS: 1.14 ms

**Reason:** One-way delay for link R1-R2: propagation 140.0 µs (28.0 km x 5 µs/km) = 0.14 ms + 1 ms equipment allowance = 1.14 ms. Target < 5 ms: MET.

**References:** IEEE 802.3ae


## VLSM Decisions

### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 10 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] HQ-Users (HQ)

**Choice:** 172.16.0.0/24

**Reason:** Subnet HQ-Users: 250 hosts requested, need 250+2 = 252 addresses, host bits = ceil(log2(252)) = 8, block size = 2^8 = 256, prefix = /24. Usable = 2^8 - 2 = 254. Utilization = 250/254 = 98.4%.

**References:** RFC 4632


### [VLSM-003] Colo-Servers (HQ)

**Choice:** 172.16.1.0/25

**Reason:** Subnet Colo-Servers: 100 hosts requested, need 100+2 = 102 addresses, host bits = ceil(log2(102)) = 7, block size = 2^7 = 128, prefix = /25. Usable = 2^7 - 2 = 126. Utilization = 100/126 = 79.4%.

**References:** RFC 4632


### [VLSM-004] R1-Users (R1)

**Choice:** 172.16.1.128/25

**Reason:** Subnet R1-Users: 120 hosts requested, need 120+2 = 122 addresses, host bits = ceil(log2(122)) = 7, block size = 2^7 = 128, prefix = /25. Usable = 2^7 - 2 = 126. Utilization = 120/126 = 95.2%.

**References:** RFC 4632


### [VLSM-005] R2-Users (R2)

**Choice:** 172.16.2.0/25

**Reason:** Subnet R2-Users: 80 hosts requested, need 80+2 = 82 addresses, host bits = ceil(log2(82)) = 7, block size = 2^7 = 128, prefix = /25. Usable = 2^7 - 2 = 126. Utilization = 80/126 = 63.5%.

**References:** RFC 4632


### [VLSM-006] P2P-HQ-R1 (HQ)

**Choice:** 172.16.2.128/30

**Reason:** Point-to-point link P2P-HQ-R1: /30, block size 4. Network + broadcast + 2 usable host addresses.

**References:** RFC 4632


### [VLSM-007] P2P-HQ-R2 (HQ)

**Choice:** 172.16.2.132/30

**Reason:** Point-to-point link P2P-HQ-R2: /30, block size 4. Network + broadcast + 2 usable host addresses.

**References:** RFC 4632


### [VLSM-008] P2P-R1-R2 (R1)

**Choice:** 172.16.2.136/30

**Reason:** Point-to-point link P2P-R1-R2: /30, block size 4. Network + broadcast + 2 usable host addresses.

**References:** RFC 4632


### [VLSM-009] Lo0-RTR-HQ (HQ)

**Choice:** 172.16.2.140/32

**Reason:** Loopback Lo0-RTR-HQ: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-010] Lo0-RTR-R1 (R1)

**Choice:** 172.16.2.141/32

**Reason:** Loopback Lo0-RTR-R1: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-011] Lo0-RTR-R2 (R2)

**Choice:** 172.16.2.142/32

**Reason:** Loopback Lo0-RTR-R2: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 10 subnets, 87.2% efficient

**Reason:** Allocated 10 subnets: 559 hosts in 641 usable addresses. Wasted: 82. Overall efficiency: 87.2%.

**References:** RFC 4632


## ROUTING Decisions

### [ROUTE-001] Protocol selection

**Choice:** OSPF single-area (Area 0)

**Reason:** Selected single-area OSPF (Area 0) because the network has 3 site(s) and 10 subnets, which is below the 50-subnet threshold for multi-area partitioning. Link-state routing provides fast convergence via SPF computation (RFC 2328).

**References:** RFC 2328


## SECURITY Decisions

### [CONFIG-RTR-HQ] Device RTR-HQ

**Choice:** Generated IOS config (104 lines)

**Reason:** Configuration for RTR-HQ (router) at site HQ: 2 SVIs, 0 trunks, 2 routed ports, OSPF, QoS.

**References:** IEEE 802.1Q, IEEE 802.1w


### [CONFIG-RTR-R1] Device RTR-R1

**Choice:** Generated IOS config (79 lines)

**Reason:** Configuration for RTR-R1 (router) at site R1: 1 SVIs, 0 trunks, 2 routed ports, OSPF, QoS.

**References:** IEEE 802.1Q, IEEE 802.1w


### [CONFIG-RTR-R2] Device RTR-R2

**Choice:** Generated IOS config (79 lines)

**Reason:** Configuration for RTR-R2 (router) at site R2: 1 SVIs, 0 trunks, 2 routed ports, OSPF, QoS.

**References:** IEEE 802.1Q, IEEE 802.1w


## Subnet Allocation Table

| Name | Site | Network | Prefix | Hosts | Usable | Util% | Gateway |
|------|------|---------|--------|-------|--------|-------|---------|
| HQ-Users | HQ | 172.16.0.0 | /24 | 250 | 254 | 98.4% | 172.16.0.1 |
| Colo-Servers | HQ | 172.16.1.0 | /25 | 100 | 126 | 79.4% | 172.16.1.1 |
| R1-Users | R1 | 172.16.1.128 | /25 | 120 | 126 | 95.2% | 172.16.1.129 |
| R2-Users | R2 | 172.16.2.0 | /25 | 80 | 126 | 63.5% | 172.16.2.1 |
| P2P-HQ-R1 | HQ | 172.16.2.128 | /30 | 2 | 2 | 100.0% | 172.16.2.129 |
| P2P-HQ-R2 | HQ | 172.16.2.132 | /30 | 2 | 2 | 100.0% | 172.16.2.133 |
| P2P-R1-R2 | R1 | 172.16.2.136 | /30 | 2 | 2 | 100.0% | 172.16.2.137 |
| Lo0-RTR-HQ | HQ | 172.16.2.140 | /32 | 1 | 1 | 100.0% | 172.16.2.140 |
| Lo0-RTR-R1 | R1 | 172.16.2.141 | /32 | 1 | 1 | 100.0% | 172.16.2.141 |
| Lo0-RTR-R2 | R2 | 172.16.2.142 | /32 | 1 | 1 | 100.0% | 172.16.2.142 |
| **TOTAL** | | | | **559** | **641** | **87.2%** | |

*Wasted addresses: 82*

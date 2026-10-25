# NetArchitect Design Rationale

## Summary Table

| # | Domain | Subject | Choice | References |
|---|--------|---------|--------|------------|
| 1 | media | Link A-Admin-B-Academic (180.0 m) | OM4 MMF, 10GBASE-SR | IEEE 802.3ae |
| 2 | media | Link A-Admin-C-Hostel (360.0 m) | OM4 MMF, 10GBASE-SR | IEEE 802.3ae |
| 3 | media | Link B-Academic-C-Hostel (250.0 m) | OM4 MMF, 10GBASE-SR | IEEE 802.3ae |
| 4 | vlsm | Site aggregate: B-Academic | 10.10.0.0/22 | RFC 4632, RFC 2328 |
| 5 | vlsm | Site aggregate: C-Hostel | 10.10.4.0/22 | RFC 4632, RFC 2328 |
| 6 | vlsm | Site aggregate: A-Admin | 10.10.8.0/23 | RFC 4632, RFC 2328 |
| 7 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 8 | vlsm | Labs (B-Academic) | 10.10.0.0/23 | RFC 4632 |
| 9 | vlsm | Faculty (B-Academic) | 10.10.2.0/24 | RFC 4632 |
| 10 | vlsm | APs (B-Academic) | 10.10.3.0/25 | RFC 4632 |
| 11 | vlsm | Allocation summary | 3 subnets, 75.3% efficient | RFC 4632 |
| 12 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 13 | vlsm | Students (C-Hostel) | 10.10.4.0/22 | RFC 4632 |
| 14 | vlsm | Allocation summary | 1 subnets, 58.7% efficient | RFC 4632 |
| 15 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 16 | vlsm | Admin (A-Admin) | 10.10.8.0/24 | RFC 4632 |
| 17 | vlsm | Mgmt (A-Admin) | 10.10.9.0/26 | RFC 4632 |
| 18 | vlsm | Servers (A-Admin) | 10.10.9.64/26 | RFC 4632 |
| 19 | vlsm | CCTV (A-Admin) | 10.10.9.128/27 | RFC 4632 |
| 20 | vlsm | Allocation summary | 4 subnets, 80.9% efficient | RFC 4632 |
| 21 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 22 | vlsm | P2P-A-Admin-B-Academic (A-Admin) | 10.10.128.0/30 | RFC 4632 |
| 23 | vlsm | P2P-A-Admin-C-Hostel (A-Admin) | 10.10.128.4/30 | RFC 4632 |
| 24 | vlsm | P2P-B-Academic-C-Hostel (B-Academic) | 10.10.128.8/30 | RFC 4632 |
| 25 | vlsm | Lo0-CORE-A (A-Admin) | 10.10.128.12/32 | RFC 4632 |
| 26 | vlsm | Lo0-DIST-B (B-Academic) | 10.10.128.13/32 | RFC 4632 |
| 27 | vlsm | Lo0-DIST-C (C-Hostel) | 10.10.128.14/32 | RFC 4632 |
| 28 | vlsm | Allocation summary | 6 subnets, 100.0% efficient | RFC 4632 |
| 29 | routing | Protocol selection | OSPF single-area (Area 0) | RFC 2328 |
| 30 | security | Device CORE-A | Generated IOS config (116 lines) | IEEE 802.1Q, IEEE 802.1w |
| 31 | security | Device DIST-B | Generated IOS config (107 lines) | IEEE 802.1Q, IEEE 802.1w |
| 32 | security | Device DIST-C | Generated IOS config (73 lines) | IEEE 802.1Q, IEEE 802.1w |

## MEDIA Decisions

### [MEDIA-002] Link A-Admin-B-Academic (180.0 m)

**Choice:** OM4 MMF, 10GBASE-SR

**Reason:** Selected OM4 Multi-Mode Fiber (10GBASE-SR, 850 nm) because link A-Admin-B-Academic distance (180.0 m) exceeds the 100 m copper limit (IEEE 802.3an) but is within the 400 m modal bandwidth limit of OM4 MMF (IEEE 802.3ae). Note: modal dispersion limits OM4 MMF to 400 m at 10 Gbps.

**References:** IEEE 802.3ae


### [MEDIA-002] Link A-Admin-C-Hostel (360.0 m)

**Choice:** OM4 MMF, 10GBASE-SR

**Reason:** Selected OM4 Multi-Mode Fiber (10GBASE-SR, 850 nm) because link A-Admin-C-Hostel distance (360.0 m) exceeds the 100 m copper limit (IEEE 802.3an) but is within the 400 m modal bandwidth limit of OM4 MMF (IEEE 802.3ae). Note: modal dispersion limits OM4 MMF to 400 m at 10 Gbps.

**References:** IEEE 802.3ae


### [MEDIA-002] Link B-Academic-C-Hostel (250.0 m)

**Choice:** OM4 MMF, 10GBASE-SR

**Reason:** Selected OM4 Multi-Mode Fiber (10GBASE-SR, 850 nm) because link B-Academic-C-Hostel distance (250.0 m) exceeds the 100 m copper limit (IEEE 802.3an) but is within the 400 m modal bandwidth limit of OM4 MMF (IEEE 802.3ae). Note: modal dispersion limits OM4 MMF to 400 m at 10 Gbps.

**References:** IEEE 802.3ae


## VLSM Decisions

### [VLSM-AGG-B-Academic] Site aggregate: B-Academic

**Choice:** 10.10.0.0/22

**Reason:** Site B-Academic aggregate: total subnet blocks = 896, rounded up to next power of 2 = 1024 (/22). This aggregate serves as the OSPF area-range summary address for B-Academic.

**References:** RFC 4632, RFC 2328


### [VLSM-AGG-C-Hostel] Site aggregate: C-Hostel

**Choice:** 10.10.4.0/22

**Reason:** Site C-Hostel aggregate: total subnet blocks = 1024, rounded up to next power of 2 = 1024 (/22). This aggregate serves as the OSPF area-range summary address for C-Hostel.

**References:** RFC 4632, RFC 2328


### [VLSM-AGG-A-Admin] Site aggregate: A-Admin

**Choice:** 10.10.8.0/23

**Reason:** Site A-Admin aggregate: total subnet blocks = 416, rounded up to next power of 2 = 512 (/23). This aggregate serves as the OSPF area-range summary address for A-Admin.

**References:** RFC 4632, RFC 2328


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 3 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] Labs (B-Academic)

**Choice:** 10.10.0.0/23

**Reason:** Subnet Labs: 300 hosts requested, need 300+2 = 302 addresses, host bits = ceil(log2(302)) = 9, block size = 2^9 = 512, prefix = /23. Usable = 2^9 - 2 = 510. Utilization = 300/510 = 58.8%.

**References:** RFC 4632


### [VLSM-003] Faculty (B-Academic)

**Choice:** 10.10.2.0/24

**Reason:** Subnet Faculty: 250 hosts requested, need 250+2 = 252 addresses, host bits = ceil(log2(252)) = 8, block size = 2^8 = 256, prefix = /24. Usable = 2^8 - 2 = 254. Utilization = 250/254 = 98.4%.

**References:** RFC 4632


### [VLSM-004] APs (B-Academic)

**Choice:** 10.10.3.0/25

**Reason:** Subnet APs: 120 hosts requested, need 120+2 = 122 addresses, host bits = ceil(log2(122)) = 7, block size = 2^7 = 128, prefix = /25. Usable = 2^7 - 2 = 126. Utilization = 120/126 = 95.2%.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 3 subnets, 75.3% efficient

**Reason:** Allocated 3 subnets: 670 hosts in 890 usable addresses. Wasted: 220. Overall efficiency: 75.3%.

**References:** RFC 4632


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 1 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] Students (C-Hostel)

**Choice:** 10.10.4.0/22

**Reason:** Subnet Students: 600 hosts requested, need 600+2 = 602 addresses, host bits = ceil(log2(602)) = 10, block size = 2^10 = 1024, prefix = /22. Usable = 2^10 - 2 = 1022. Utilization = 600/1022 = 58.7%.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 1 subnets, 58.7% efficient

**Reason:** Allocated 1 subnets: 600 hosts in 1022 usable addresses. Wasted: 422. Overall efficiency: 58.7%.

**References:** RFC 4632


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 4 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] Admin (A-Admin)

**Choice:** 10.10.8.0/24

**Reason:** Subnet Admin: 200 hosts requested, need 200+2 = 202 addresses, host bits = ceil(log2(202)) = 8, block size = 2^8 = 256, prefix = /24. Usable = 2^8 - 2 = 254. Utilization = 200/254 = 78.7%.

**References:** RFC 4632


### [VLSM-003] Mgmt (A-Admin)

**Choice:** 10.10.9.0/26

**Reason:** Subnet Mgmt: 40 hosts requested, need 40+2 = 42 addresses, host bits = ceil(log2(42)) = 6, block size = 2^6 = 64, prefix = /26. Usable = 2^6 - 2 = 62. Utilization = 40/62 = 64.5%.

**References:** RFC 4632


### [VLSM-004] Servers (A-Admin)

**Choice:** 10.10.9.64/26

**Reason:** Subnet Servers: 60 hosts requested, need 60+2 = 62 addresses, host bits = ceil(log2(62)) = 6, block size = 2^6 = 64, prefix = /26. Usable = 2^6 - 2 = 62. Utilization = 60/62 = 96.8%.

**References:** RFC 4632


### [VLSM-005] CCTV (A-Admin)

**Choice:** 10.10.9.128/27

**Reason:** Subnet CCTV: 30 hosts requested, need 30+2 = 32 addresses, host bits = ceil(log2(32)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 30/30 = 100.0%.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 4 subnets, 80.9% efficient

**Reason:** Allocated 4 subnets: 330 hosts in 408 usable addresses. Wasted: 78. Overall efficiency: 80.9%.

**References:** RFC 4632


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 6 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] P2P-A-Admin-B-Academic (A-Admin)

**Choice:** 10.10.128.0/30

**Reason:** Point-to-point link P2P-A-Admin-B-Academic: /30, block size 4. Network + broadcast + 2 usable host addresses.

**References:** RFC 4632


### [VLSM-003] P2P-A-Admin-C-Hostel (A-Admin)

**Choice:** 10.10.128.4/30

**Reason:** Point-to-point link P2P-A-Admin-C-Hostel: /30, block size 4. Network + broadcast + 2 usable host addresses.

**References:** RFC 4632


### [VLSM-004] P2P-B-Academic-C-Hostel (B-Academic)

**Choice:** 10.10.128.8/30

**Reason:** Point-to-point link P2P-B-Academic-C-Hostel: /30, block size 4. Network + broadcast + 2 usable host addresses.

**References:** RFC 4632


### [VLSM-005] Lo0-CORE-A (A-Admin)

**Choice:** 10.10.128.12/32

**Reason:** Loopback Lo0-CORE-A: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-006] Lo0-DIST-B (B-Academic)

**Choice:** 10.10.128.13/32

**Reason:** Loopback Lo0-DIST-B: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-007] Lo0-DIST-C (C-Hostel)

**Choice:** 10.10.128.14/32

**Reason:** Loopback Lo0-DIST-C: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 6 subnets, 100.0% efficient

**Reason:** Allocated 6 subnets: 9 hosts in 9 usable addresses. Wasted: 0. Overall efficiency: 100.0%.

**References:** RFC 4632


## ROUTING Decisions

### [ROUTE-001] Protocol selection

**Choice:** OSPF single-area (Area 0)

**Reason:** Selected single-area OSPF (Area 0) because the network has 3 site(s) and 14 subnets, which is below the 50-subnet threshold for multi-area partitioning. Link-state routing provides fast convergence via SPF computation (RFC 2328).

**References:** RFC 2328


## SECURITY Decisions

### [CONFIG-CORE-A] Device CORE-A

**Choice:** Generated IOS config (116 lines)

**Reason:** Configuration for CORE-A (l3_switch) at site A-Admin: 4 SVIs, 0 trunks, 2 routed ports, OSPF.

**References:** IEEE 802.1Q, IEEE 802.1w


### [CONFIG-DIST-B] Device DIST-B

**Choice:** Generated IOS config (107 lines)

**Reason:** Configuration for DIST-B (l3_switch) at site B-Academic: 3 SVIs, 0 trunks, 2 routed ports, OSPF.

**References:** IEEE 802.1Q, IEEE 802.1w


### [CONFIG-DIST-C] Device DIST-C

**Choice:** Generated IOS config (73 lines)

**Reason:** Configuration for DIST-C (l3_switch) at site C-Hostel: 1 SVIs, 0 trunks, 2 routed ports, OSPF.

**References:** IEEE 802.1Q, IEEE 802.1w


## Subnet Allocation Table

| Name | Site | Network | Prefix | Hosts | Usable | Util% | Gateway |
|------|------|---------|--------|-------|--------|-------|---------|
| Labs | B-Academic | 10.10.0.0 | /23 | 300 | 510 | 58.8% | 10.10.0.1 |
| Faculty | B-Academic | 10.10.2.0 | /24 | 250 | 254 | 98.4% | 10.10.2.1 |
| APs | B-Academic | 10.10.3.0 | /25 | 120 | 126 | 95.2% | 10.10.3.1 |
| Students | C-Hostel | 10.10.4.0 | /22 | 600 | 1022 | 58.7% | 10.10.4.1 |
| Admin | A-Admin | 10.10.8.0 | /24 | 200 | 254 | 78.7% | 10.10.8.1 |
| Mgmt | A-Admin | 10.10.9.0 | /26 | 40 | 62 | 64.5% | 10.10.9.1 |
| Servers | A-Admin | 10.10.9.64 | /26 | 60 | 62 | 96.8% | 10.10.9.65 |
| CCTV | A-Admin | 10.10.9.128 | /27 | 30 | 30 | 100.0% | 10.10.9.129 |
| P2P-A-Admin-B-Academic | A-Admin | 10.10.128.0 | /30 | 2 | 2 | 100.0% | 10.10.128.1 |
| P2P-A-Admin-C-Hostel | A-Admin | 10.10.128.4 | /30 | 2 | 2 | 100.0% | 10.10.128.5 |
| P2P-B-Academic-C-Hostel | B-Academic | 10.10.128.8 | /30 | 2 | 2 | 100.0% | 10.10.128.9 |
| Lo0-CORE-A | A-Admin | 10.10.128.12 | /32 | 1 | 1 | 100.0% | 10.10.128.12 |
| Lo0-DIST-B | B-Academic | 10.10.128.13 | /32 | 1 | 1 | 100.0% | 10.10.128.13 |
| Lo0-DIST-C | C-Hostel | 10.10.128.14 | /32 | 1 | 1 | 100.0% | 10.10.128.14 |
| **TOTAL** | | | | **1609** | **2329** | **69.1%** | |

*Wasted addresses: 720*

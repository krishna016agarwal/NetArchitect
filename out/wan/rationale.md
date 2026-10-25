# NetArchitect Design Rationale

## Summary Table

| # | Domain | Subject | Choice | References |
|---|--------|---------|--------|------------|
| 1 | media | Link Delhi-Mumbai (1150.0 km) | Carrier WAN circuit (IPsec secured) | RFC 4301 |
| 2 | media | Link Delhi-Bengaluru (1750.0 km) | Carrier WAN circuit (IPsec secured) | RFC 4301 |
| 3 | media | Link Delhi-Chennai (1760.0 km) | Carrier WAN circuit (IPsec secured) | RFC 4301 |
| 4 | vlsm | Site aggregate: Delhi | 10.100.0.0/21 | RFC 4632, RFC 2328 |
| 5 | vlsm | Site aggregate: Bengaluru | 10.100.8.0/22 | RFC 4632, RFC 2328 |
| 6 | vlsm | Site aggregate: Chennai | 10.100.12.0/22 | RFC 4632, RFC 2328 |
| 7 | vlsm | Site aggregate: Mumbai | 10.100.16.0/22 | RFC 4632, RFC 2328 |
| 8 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 9 | vlsm | Delhi-IoT (Delhi) | 10.100.0.0/22 | RFC 4632 |
| 10 | vlsm | Delhi-Mgmt (Delhi) | 10.100.4.0/27 | RFC 4632 |
| 11 | vlsm | Delhi-Servers (Delhi) | 10.100.4.32/27 | RFC 4632 |
| 12 | vlsm | Allocation summary | 3 subnets, 78.6% efficient | RFC 4632 |
| 13 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 14 | vlsm | Bengaluru-IoT (Bengaluru) | 10.100.8.0/23 | RFC 4632 |
| 15 | vlsm | Bengaluru-Mgmt (Bengaluru) | 10.100.10.0/27 | RFC 4632 |
| 16 | vlsm | Bengaluru-Servers (Bengaluru) | 10.100.10.32/27 | RFC 4632 |
| 17 | vlsm | Allocation summary | 3 subnets, 78.9% efficient | RFC 4632 |
| 18 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 19 | vlsm | Chennai-IoT (Chennai) | 10.100.12.0/23 | RFC 4632 |
| 20 | vlsm | Chennai-Mgmt (Chennai) | 10.100.14.0/27 | RFC 4632 |
| 21 | vlsm | Chennai-Servers (Chennai) | 10.100.14.32/27 | RFC 4632 |
| 22 | vlsm | Allocation summary | 3 subnets, 61.4% efficient | RFC 4632 |
| 23 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 24 | vlsm | Mumbai-IoT (Mumbai) | 10.100.16.0/23 | RFC 4632 |
| 25 | vlsm | Mumbai-Mgmt (Mumbai) | 10.100.18.0/27 | RFC 4632 |
| 26 | vlsm | Mumbai-Servers (Mumbai) | 10.100.18.32/27 | RFC 4632 |
| 27 | vlsm | Allocation summary | 3 subnets, 96.5% efficient | RFC 4632 |
| 28 | vlsm | Allocation order | Descending by block size | RFC 4632 |
| 29 | vlsm | P2P-Delhi-Bengaluru (Delhi) | 10.100.128.0/31 | RFC 4632, RFC 3021 |
| 30 | vlsm | P2P-Delhi-Chennai (Delhi) | 10.100.128.2/31 | RFC 4632, RFC 3021 |
| 31 | vlsm | P2P-Delhi-Mumbai (Delhi) | 10.100.128.4/31 | RFC 4632, RFC 3021 |
| 32 | vlsm | Lo0-RTR-BENGALURU (Bengaluru) | 10.100.128.6/32 | RFC 4632 |
| 33 | vlsm | Lo0-RTR-CHENNAI (Chennai) | 10.100.128.7/32 | RFC 4632 |
| 34 | vlsm | Lo0-RTR-DELHI (Delhi) | 10.100.128.8/32 | RFC 4632 |
| 35 | vlsm | Lo0-RTR-MUMBAI (Mumbai) | 10.100.128.9/32 | RFC 4632 |
| 36 | vlsm | Allocation summary | 7 subnets, 100.0% efficient | RFC 4632 |
| 37 | routing | Protocol selection | Multi-area OSPF + eBGP (ASN 65001 <-> 65010) | RFC 2328, RFC 4271, RFC 6996 |
| 38 | security | Device RTR-DELHI | Generated IOS config (136 lines) | IEEE 802.1Q, IEEE 802.1w |
| 39 | security | Device RTR-MUMBAI | Generated IOS config (88 lines) | IEEE 802.1Q, IEEE 802.1w |
| 40 | security | Device RTR-BENGALURU | Generated IOS config (88 lines) | IEEE 802.1Q, IEEE 802.1w |
| 41 | security | Device RTR-CHENNAI | Generated IOS config (88 lines) | IEEE 802.1Q, IEEE 802.1w |

## MEDIA Decisions

### [MEDIA-003] Link Delhi-Mumbai (1150.0 km)

**Choice:** Carrier WAN circuit (IPsec secured)

**Reason:** Selected Carrier WAN circuit because link Delhi-Mumbai distance (1150.0 km) exceeds the 80 km limit for owned fiber. Recommend a carrier WAN circuit secured with IPsec instead of owned fiber.

**References:** RFC 4301


### [MEDIA-003] Link Delhi-Bengaluru (1750.0 km)

**Choice:** Carrier WAN circuit (IPsec secured)

**Reason:** Selected Carrier WAN circuit because link Delhi-Bengaluru distance (1750.0 km) exceeds the 80 km limit for owned fiber. Recommend a carrier WAN circuit secured with IPsec instead of owned fiber.

**References:** RFC 4301


### [MEDIA-003] Link Delhi-Chennai (1760.0 km)

**Choice:** Carrier WAN circuit (IPsec secured)

**Reason:** Selected Carrier WAN circuit because link Delhi-Chennai distance (1760.0 km) exceeds the 80 km limit for owned fiber. Recommend a carrier WAN circuit secured with IPsec instead of owned fiber.

**References:** RFC 4301


## VLSM Decisions

### [VLSM-AGG-Delhi] Site aggregate: Delhi

**Choice:** 10.100.0.0/21

**Reason:** Site Delhi aggregate: total subnet blocks = 1088, rounded up to next power of 2 = 2048 (/21). This aggregate serves as the OSPF area-range summary address for Delhi.

**References:** RFC 4632, RFC 2328


### [VLSM-AGG-Bengaluru] Site aggregate: Bengaluru

**Choice:** 10.100.8.0/22

**Reason:** Site Bengaluru aggregate: total subnet blocks = 576, rounded up to next power of 2 = 1024 (/22). This aggregate serves as the OSPF area-range summary address for Bengaluru.

**References:** RFC 4632, RFC 2328


### [VLSM-AGG-Chennai] Site aggregate: Chennai

**Choice:** 10.100.12.0/22

**Reason:** Site Chennai aggregate: total subnet blocks = 576, rounded up to next power of 2 = 1024 (/22). This aggregate serves as the OSPF area-range summary address for Chennai.

**References:** RFC 4632, RFC 2328


### [VLSM-AGG-Mumbai] Site aggregate: Mumbai

**Choice:** 10.100.16.0/22

**Reason:** Site Mumbai aggregate: total subnet blocks = 576, rounded up to next power of 2 = 1024 (/22). This aggregate serves as the OSPF area-range summary address for Mumbai.

**References:** RFC 4632, RFC 2328


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 3 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] Delhi-IoT (Delhi)

**Choice:** 10.100.0.0/22

**Reason:** Subnet Delhi-IoT: 800 hosts requested, need 800+2 = 802 addresses, host bits = ceil(log2(802)) = 10, block size = 2^10 = 1024, prefix = /22. Usable = 2^10 - 2 = 1022. Utilization = 800/1022 = 78.3%.

**References:** RFC 4632


### [VLSM-003] Delhi-Mgmt (Delhi)

**Choice:** 10.100.4.0/27

**Reason:** Subnet Delhi-Mgmt: 30 hosts requested, need 30+2 = 32 addresses, host bits = ceil(log2(32)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 30/30 = 100.0%.

**References:** RFC 4632


### [VLSM-004] Delhi-Servers (Delhi)

**Choice:** 10.100.4.32/27

**Reason:** Subnet Delhi-Servers: 20 hosts requested, need 20+2 = 22 addresses, host bits = ceil(log2(22)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 20/30 = 66.7%.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 3 subnets, 78.6% efficient

**Reason:** Allocated 3 subnets: 850 hosts in 1082 usable addresses. Wasted: 232. Overall efficiency: 78.6%.

**References:** RFC 4632


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 3 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] Bengaluru-IoT (Bengaluru)

**Choice:** 10.100.8.0/23

**Reason:** Subnet Bengaluru-IoT: 400 hosts requested, need 400+2 = 402 addresses, host bits = ceil(log2(402)) = 9, block size = 2^9 = 512, prefix = /23. Usable = 2^9 - 2 = 510. Utilization = 400/510 = 78.4%.

**References:** RFC 4632


### [VLSM-003] Bengaluru-Mgmt (Bengaluru)

**Choice:** 10.100.10.0/27

**Reason:** Subnet Bengaluru-Mgmt: 30 hosts requested, need 30+2 = 32 addresses, host bits = ceil(log2(32)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 30/30 = 100.0%.

**References:** RFC 4632


### [VLSM-004] Bengaluru-Servers (Bengaluru)

**Choice:** 10.100.10.32/27

**Reason:** Subnet Bengaluru-Servers: 20 hosts requested, need 20+2 = 22 addresses, host bits = ceil(log2(22)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 20/30 = 66.7%.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 3 subnets, 78.9% efficient

**Reason:** Allocated 3 subnets: 450 hosts in 570 usable addresses. Wasted: 120. Overall efficiency: 78.9%.

**References:** RFC 4632


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 3 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] Chennai-IoT (Chennai)

**Choice:** 10.100.12.0/23

**Reason:** Subnet Chennai-IoT: 300 hosts requested, need 300+2 = 302 addresses, host bits = ceil(log2(302)) = 9, block size = 2^9 = 512, prefix = /23. Usable = 2^9 - 2 = 510. Utilization = 300/510 = 58.8%.

**References:** RFC 4632


### [VLSM-003] Chennai-Mgmt (Chennai)

**Choice:** 10.100.14.0/27

**Reason:** Subnet Chennai-Mgmt: 30 hosts requested, need 30+2 = 32 addresses, host bits = ceil(log2(32)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 30/30 = 100.0%.

**References:** RFC 4632


### [VLSM-004] Chennai-Servers (Chennai)

**Choice:** 10.100.14.32/27

**Reason:** Subnet Chennai-Servers: 20 hosts requested, need 20+2 = 22 addresses, host bits = ceil(log2(22)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 20/30 = 66.7%.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 3 subnets, 61.4% efficient

**Reason:** Allocated 3 subnets: 350 hosts in 570 usable addresses. Wasted: 220. Overall efficiency: 61.4%.

**References:** RFC 4632


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 3 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] Mumbai-IoT (Mumbai)

**Choice:** 10.100.16.0/23

**Reason:** Subnet Mumbai-IoT: 500 hosts requested, need 500+2 = 502 addresses, host bits = ceil(log2(502)) = 9, block size = 2^9 = 512, prefix = /23. Usable = 2^9 - 2 = 510. Utilization = 500/510 = 98.0%.

**References:** RFC 4632


### [VLSM-003] Mumbai-Mgmt (Mumbai)

**Choice:** 10.100.18.0/27

**Reason:** Subnet Mumbai-Mgmt: 30 hosts requested, need 30+2 = 32 addresses, host bits = ceil(log2(32)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 30/30 = 100.0%.

**References:** RFC 4632


### [VLSM-004] Mumbai-Servers (Mumbai)

**Choice:** 10.100.18.32/27

**Reason:** Subnet Mumbai-Servers: 20 hosts requested, need 20+2 = 22 addresses, host bits = ceil(log2(22)) = 5, block size = 2^5 = 32, prefix = /27. Usable = 2^5 - 2 = 30. Utilization = 20/30 = 66.7%.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 3 subnets, 96.5% efficient

**Reason:** Allocated 3 subnets: 550 hosts in 570 usable addresses. Wasted: 20. Overall efficiency: 96.5%.

**References:** RFC 4632


### [VLSM-001] Allocation order

**Choice:** Descending by block size

**Reason:** Sorted 7 subnet requests in descending order by block size to minimize address space fragmentation. Largest subnets are allocated first, ensuring natural alignment without wasted gaps.

**References:** RFC 4632


### [VLSM-002] P2P-Delhi-Bengaluru (Delhi)

**Choice:** 10.100.128.0/31

**Reason:** Point-to-point link P2P-Delhi-Bengaluru: /31 (RFC 3021), block size 2. RFC 3021 allows both addresses to be usable.

**References:** RFC 4632, RFC 3021


### [VLSM-003] P2P-Delhi-Chennai (Delhi)

**Choice:** 10.100.128.2/31

**Reason:** Point-to-point link P2P-Delhi-Chennai: /31 (RFC 3021), block size 2. RFC 3021 allows both addresses to be usable.

**References:** RFC 4632, RFC 3021


### [VLSM-004] P2P-Delhi-Mumbai (Delhi)

**Choice:** 10.100.128.4/31

**Reason:** Point-to-point link P2P-Delhi-Mumbai: /31 (RFC 3021), block size 2. RFC 3021 allows both addresses to be usable.

**References:** RFC 4632, RFC 3021


### [VLSM-005] Lo0-RTR-BENGALURU (Bengaluru)

**Choice:** 10.100.128.6/32

**Reason:** Loopback Lo0-RTR-BENGALURU: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-006] Lo0-RTR-CHENNAI (Chennai)

**Choice:** 10.100.128.7/32

**Reason:** Loopback Lo0-RTR-CHENNAI: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-007] Lo0-RTR-DELHI (Delhi)

**Choice:** 10.100.128.8/32

**Reason:** Loopback Lo0-RTR-DELHI: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-008] Lo0-RTR-MUMBAI (Mumbai)

**Choice:** 10.100.128.9/32

**Reason:** Loopback Lo0-RTR-MUMBAI: /32 host route, 1 address.

**References:** RFC 4632


### [VLSM-SUMMARY] Allocation summary

**Choice:** 7 subnets, 100.0% efficient

**Reason:** Allocated 7 subnets: 10 hosts in 10 usable addresses. Wasted: 0. Overall efficiency: 100.0%.

**References:** RFC 4632


## ROUTING Decisions

### [ROUTE-002] Protocol selection

**Choice:** Multi-area OSPF + eBGP (ASN 65001 <-> 65010)

**Reason:** Selected multi-area OSPF because the network spans 4 sites with 19 subnets. Each city gets its own OSPF area for LSA containment and summarization via area-range on ABRs (RFC 2328). eBGP connects on-premises ASN 65001 to cloud ASN 65010 for external reachability (RFC 4271, RFC 6996 private ASNs).

**References:** RFC 2328, RFC 4271, RFC 6996


## SECURITY Decisions

### [CONFIG-RTR-DELHI] Device RTR-DELHI

**Choice:** Generated IOS config (136 lines)

**Reason:** Configuration for RTR-DELHI (router) at site Delhi: 3 SVIs, 0 trunks, 3 routed ports, OSPF, BGP, IPsec.

**References:** IEEE 802.1Q, IEEE 802.1w


### [CONFIG-RTR-MUMBAI] Device RTR-MUMBAI

**Choice:** Generated IOS config (88 lines)

**Reason:** Configuration for RTR-MUMBAI (router) at site Mumbai: 3 SVIs, 0 trunks, 1 routed ports, OSPF.

**References:** IEEE 802.1Q, IEEE 802.1w


### [CONFIG-RTR-BENGALURU] Device RTR-BENGALURU

**Choice:** Generated IOS config (88 lines)

**Reason:** Configuration for RTR-BENGALURU (router) at site Bengaluru: 3 SVIs, 0 trunks, 1 routed ports, OSPF.

**References:** IEEE 802.1Q, IEEE 802.1w


### [CONFIG-RTR-CHENNAI] Device RTR-CHENNAI

**Choice:** Generated IOS config (88 lines)

**Reason:** Configuration for RTR-CHENNAI (router) at site Chennai: 3 SVIs, 0 trunks, 1 routed ports, OSPF.

**References:** IEEE 802.1Q, IEEE 802.1w


## Subnet Allocation Table

| Name | Site | Network | Prefix | Hosts | Usable | Util% | Gateway |
|------|------|---------|--------|-------|--------|-------|---------|
| Delhi-IoT | Delhi | 10.100.0.0 | /22 | 800 | 1022 | 78.3% | 10.100.0.1 |
| Delhi-Mgmt | Delhi | 10.100.4.0 | /27 | 30 | 30 | 100.0% | 10.100.4.1 |
| Delhi-Servers | Delhi | 10.100.4.32 | /27 | 20 | 30 | 66.7% | 10.100.4.33 |
| Bengaluru-IoT | Bengaluru | 10.100.8.0 | /23 | 400 | 510 | 78.4% | 10.100.8.1 |
| Bengaluru-Mgmt | Bengaluru | 10.100.10.0 | /27 | 30 | 30 | 100.0% | 10.100.10.1 |
| Bengaluru-Servers | Bengaluru | 10.100.10.32 | /27 | 20 | 30 | 66.7% | 10.100.10.33 |
| Chennai-IoT | Chennai | 10.100.12.0 | /23 | 300 | 510 | 58.8% | 10.100.12.1 |
| Chennai-Mgmt | Chennai | 10.100.14.0 | /27 | 30 | 30 | 100.0% | 10.100.14.1 |
| Chennai-Servers | Chennai | 10.100.14.32 | /27 | 20 | 30 | 66.7% | 10.100.14.33 |
| Mumbai-IoT | Mumbai | 10.100.16.0 | /23 | 500 | 510 | 98.0% | 10.100.16.1 |
| Mumbai-Mgmt | Mumbai | 10.100.18.0 | /27 | 30 | 30 | 100.0% | 10.100.18.1 |
| Mumbai-Servers | Mumbai | 10.100.18.32 | /27 | 20 | 30 | 66.7% | 10.100.18.33 |
| P2P-Delhi-Bengaluru | Delhi | 10.100.128.0 | /31 | 2 | 2 | 100.0% | 10.100.128.0 |
| P2P-Delhi-Chennai | Delhi | 10.100.128.2 | /31 | 2 | 2 | 100.0% | 10.100.128.2 |
| P2P-Delhi-Mumbai | Delhi | 10.100.128.4 | /31 | 2 | 2 | 100.0% | 10.100.128.4 |
| Lo0-RTR-BENGALURU | Bengaluru | 10.100.128.6 | /32 | 1 | 1 | 100.0% | 10.100.128.6 |
| Lo0-RTR-CHENNAI | Chennai | 10.100.128.7 | /32 | 1 | 1 | 100.0% | 10.100.128.7 |
| Lo0-RTR-DELHI | Delhi | 10.100.128.8 | /32 | 1 | 1 | 100.0% | 10.100.128.8 |
| Lo0-RTR-MUMBAI | Mumbai | 10.100.128.9 | /32 | 1 | 1 | 100.0% | 10.100.128.9 |
| **TOTAL** | | | | **2210** | **2802** | **78.9%** | |

*Wasted addresses: 592*

# NetArchitect — CLI Network Design & Cisco IOS Configuration Generator

**Course:** CIC-307 (Computer Networks Mini-Project)  
**Author:** Krishna Agarwal | Piyush Verma
**Repository:** [https://github.com/krishna016agarwal/NetArchitect.git](https://github.com/krishna016agarwal/NetArchitect.git)  
**Architecture:** Python 3.11+ Standard Library + Jinja2 + Pytest

NetArchitect is an automated, explainable network design CLI tool. It takes physical and logical network requirements as input (either via built-in presets or custom JSON scenarios), applies deterministic rule engines for physical media selection, bitwise VLSM allocation, and routing protocol selection, and outputs ready-to-deploy Cisco IOS configurations, natural-language justifications, and full IP allocation tables.

---

## Key Submission Deliverables

This repository contains all required deliverables for course evaluation:

| Deliverable | Location in Repository | Description |
|---|---|---|
| **1. Source Code Repository** | `netarchitect/`<br>`tests/` | Clean Python 3.11+ codebase, CLI entrypoint, rule engines, Jinja2 config generator, and a comprehensive 50-test pytest suite. |
| **2. AI Code Audit Report** | [`ai_audit_log.md`](ai_audit_log.md)<br>`audit_lab/` | In-depth empirical quality audit analyzing real AI first-draft defects, bit-level root causes, packet-flow analysis, and fixed diffs. |
| **3. Verification Exports** | [`out/campus/campus_full_config.txt`](out/campus/campus_full_config.txt)<br>[`out/metro/metro_full_config.txt`](out/metro/metro_full_config.txt)<br>[`out/wan/wan_full_config.txt`](out/wan/wan_full_config.txt) | Exported Cisco IOS configuration files from the 3 preset profiles, validated and ready to paste directly into Cisco Packet Tracer or GNS3. |

---

## Architecture Diagram

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                           NETARCHITECT PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                                INPUT                                  │
 │   - Built-in Presets: campus, metro, wan                              │
 │   - Custom JSON Scenarios: sites, devices, links, VLANs, resiliency   │
 └───────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                           L1/L2 MEDIA ENGINE                          │
 │   - <= 100 m: Cat6a UTP, 10GBASE-T (IEEE 802.3an)                     │
 │   - 101–400 m: OM4 Multimode Fiber, 10GBASE-SR (IEEE 802.3ae)         │
 │   - 401 m–80 km: OS2 Single-Mode Fiber (LR / ER / ZR Selection)       │
 │   - > 80 km: Carrier WAN Circuit with IPsec (RFC 4301)                │
 │   - Physics-based Optical Power Budget & Link Margin Calculation      │
 └───────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                         L3 VLSM & ROUTING ENGINE                      │
 │   - Pure Bitwise Integer Subnet Math (Zero 'ipaddress' in Engine)     │
 │   - Prefix, Mask, Wildcard, Broadcast, Usable Range, Alignment        │
 │   - Flat Mode (Campus/Metro) & Hierarchical Supernets (WAN)           │
 │   - Single-Area OSPF (RFC 2328), Multi-Area OSPF, eBGP (RFC 4271)     │
 └───────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌───────────────────────────────────────────────────────────────────────┐
 │                         EXPLAINABLE EXPORTER                          │
 │   - Cisco IOS Configs: Full merged config + per-device configs        │
 │   - Strict ios_allowlist.py Prefix Validation & L2/L3 Hardening       │
 │   - rationale.md: Complete engineering justification per decision     │
 │   - allocation.csv: Full IP address allocation and utilization table  │
 │   - summary.json: Machine-readable architecture summary               │
 └───────────────────────────────────────────────────────────────────────┘
```

---

## Verification Exports & Packet Tracer Guide

The `out/` directory contains complete exported Cisco IOS configurations for all 3 network design scenarios:

### 1. Campus LAN Profile (`out/campus/`)
- **Scale:** 1,600 hosts across 3 campus buildings (Admin, Academic, Hostel).
- **Topology:** Layer 3 switch triangle (`CORE-A`, `DIST-B`, `DIST-C`) with Rapid-PVST+, SVIs, PortFast, BPDU Guard, and single-area OSPF (Area 0).
- **Files:**
  - Full Merged Config: [`out/campus/campus_full_config.txt`](out/campus/campus_full_config.txt)
  - Per-Device: `out/campus/configs/CORE-A.txt`, `DIST-B.txt`, `DIST-C.txt`
  - Rationale: [`out/campus/rationale.md`](out/campus/rationale.md)
  - Allocation Table: [`out/campus/allocation.csv`](out/campus/allocation.csv)

### 2. Metro MAN Profile (`out/metro/`)
- **Scale:** 550 hosts connecting HQ and 2 remote branches over OS2 single-mode fiber (15–35 km).
- **Topology:** Dual-homed failover topology (`RTR-HQ`, `RTR-R1`, `RTR-R2`), EVPL 802.1Q subinterfaces, and QoS priority queuing target $< 5\text{ ms}$.
- **Files:**
  - Full Merged Config: [`out/metro/metro_full_config.txt`](out/metro/metro_full_config.txt)
  - Per-Device: `out/metro/configs/RTR-HQ.txt`, `RTR-R1.txt`, `RTR-R2.txt`
  - Rationale: [`out/metro/rationale.md`](out/metro/rationale.md)
  - Allocation Table: [`out/metro/allocation.csv`](out/metro/allocation.csv)

### 3. Global WAN Profile (`out/wan/`)
- **Scale:** 2,200+ IoT and enterprise hosts across 4 Indian cities (Delhi, Mumbai, Bengaluru, Chennai) + AWS/Azure Cloud VPC (`10.200.0.0/16`).
- **Topology:** Hub-and-spoke routers (`RTR-DELHI`, `RTR-MUMBAI`, `RTR-BENGALURU`, `RTR-CHENNAI`), hierarchical VLSM supernetting, multi-area OSPF summarization on ABRs, and eBGP (ASN 65001 $\leftrightarrow$ 65010) over IPsec tunnel.
- **Files:**
  - Full Merged Config: [`out/wan/wan_full_config.txt`](out/wan/wan_full_config.txt)
  - Per-Device: `out/wan/configs/RTR-DELHI.txt`, `RTR-MUMBAI.txt`, `RTR-BENGALURU.txt`, `RTR-CHENNAI.txt`
  - Rationale: [`out/wan/rationale.md`](out/wan/rationale.md)
  - Allocation Table: [`out/wan/allocation.csv`](out/wan/allocation.csv)

### How to Load into Cisco Packet Tracer or GNS3
1. Launch Packet Tracer and add the switches or routers specified in the profile.
2. Interconnect interfaces according to the link descriptions.
3. Open each device's CLI tab, enter `configure terminal`, and paste the contents of `out/<profile>/configs/<device>.txt`.
4. Run standard verification commands:
   ```cisco
   show ip interface brief
   show vlan brief
   show ip route
   show ip ospf neighbor
   show interfaces trunk
   ```

---

## Installation & Setup

### Prerequisites
- Python 3.11+
- pip package manager

### Install Dependencies
```bash
python -m pip install jinja2 pytest
```

---

## Usage Instructions

### 1. Running Built-In Presets
Run any preset from the terminal:
```bash
# Campus LAN
python -m netarchitect run --preset campus --out out/

# Metro MAN
python -m netarchitect run --preset metro --out out/

# Global WAN
python -m netarchitect run --preset wan --out out/
```

### 2. Running a Custom Network Scenario
You can define custom parameters in a JSON file and run:
```bash
python -m netarchitect run --custom path/to/my_network.json --out out/
```

---

## Running the Automated Test Suite

NetArchitect features a 50-test automated verification suite using `pytest`:

```bash
# Run all tests with detailed verbosity
python -m pytest tests/ -v

# Run individual test modules
python -m pytest tests/test_media.py -v
python -m pytest tests/test_vlsm.py -v
python -m pytest tests/test_configgen.py -v
python -m pytest tests/test_presets.py -v
python -m pytest tests/test_mutation.py -v
```

---

## Key Design Principles & Standards Compliance

1. **Deterministic Bitwise Subnet Arithmetic**:
   All subnet sizing, host bits, masks, wildcards, network boundaries, and broadcast addresses are computed using integer bit operations (`<<`, `>>`, `&`, `|`, `^`, `~`). The `ipaddress` module is strictly banned from the engine and used solely in tests as an independent oracle.
2. **Standardized Optical Constants**:
   Transceiver reach, wavelength, attenuation coefficients ($0.35\text{ dB/km}$ at 1310 nm, $0.25\text{ dB/km}$ at 1550 nm), connector loss ($0.5\text{ dB} \times 4$), splice loss, and safety margin ($2.0\text{ dB}$) are centralized in `netarchitect/constants.py`.
3. **Cisco IOS Command Allowlist**:
   Every generated configuration line is validated against `netarchitect/ios_allowlist.py` to prevent invalid commands or configuration hallucinations.
4. **Security Best Practices**:
   - Access ports enforce `spanning-tree portfast` and `spanning-tree bpduguard enable`.
   - Trunk ports enforce explicit `switchport trunk allowed vlan` lists and dedicated Native VLAN 999.
   - Access-facing SVIs enforce `passive-interface` to isolate routing protocol control planes.

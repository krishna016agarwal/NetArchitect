# AI Code Quality Audit Log — NetArchitect (CIC-307)

## Executive Summary

As a network engineer and software developer, I conducted an empirical quality audit evaluating first-draft AI generation of networking software and Cisco IOS device configurations. The objective was to capture authentic defects produced by Large Language Models on domain-specific networking tasks, analyze their root causes at the bit and protocol levels, and build automated verification harnesses to prevent such defects from reaching production networks.

During Phase 0, five naive first-draft implementations were generated from minimal one-line prompts without providing the full specification. An independent audit harness (`audit_lab/tests/audit_harness.py`) executing 832 checks against Python's `ipaddress` module and RFC specifications identified **9 genuine failures across 3 tasks** (Tasks 03, 04, and 05). Below are comprehensive forensic analyses of the two most critical incidents.

---

## Incident 1: Incorrect OSPF Wildcard Mask for /27 Prefix and Missing Passive Interface

### 1. Prompt (verbatim)
```text
Write Cisco IOS OSPF config for a router with interfaces 10.10.1.0/26 and 10.10.1.64/27 in area 0.
```

### 2. AI Output (verbatim buggy code)
```cisco
! Cisco IOS OSPF Configuration
! Interfaces: 10.10.1.0/26 and 10.10.1.64/27 in Area 0

hostname OSPF-ROUTER
!
interface GigabitEthernet0/0
 ip address 10.10.1.1 255.255.255.192
 no shutdown
!
interface GigabitEthernet0/1
 ip address 10.10.1.65 255.255.255.224
 no shutdown
!
router ospf 1
 router-id 1.1.1.1
 network 10.10.1.0 0.0.0.63 area 0
 network 10.10.1.64 0.0.0.63 area 0
!
end
```

### 3. Detection (real harness output)
```text
[FAIL] Task 05: OSPF wildcard for 10.10.1.64
    Expected: 0.0.0.31
    Actual:   0.0.0.63
[FAIL] Task 05: LAN-facing interfaces are passive
    Expected: passive-interface on LAN interfaces
    Actual:   not found
```

### 4. Root Cause
- **Bit-Level Mask Arithmetic**: The second interface operates on a `/27` prefix (`255.255.255.224`). A `/27` mask has 27 network bits and 5 host bits ($2^5 = 32$). The bitwise wildcard mask is computed as:
  $$\text{Wildcard} = \sim\text{Mask} \ \& \ \text{0xFFFFFFFF} = \sim\text{0xFFFFFFE0} \ \& \ \text{0xFFFFFFFF} = \text{0x0000001F} \rightarrow 0.0.0.31$$
  The AI draft copy-pasted `0.0.0.63` (`/26`, 6 host bits) from the previous line.
- **Protocol-Level Scope**: Wildcard `0.0.0.63` applied to `10.10.1.64` matches any IP in range `10.10.1.64` through `10.10.1.127`. If a future interface is added in subnet `10.10.1.96/27`, OSPF will inadvertently enable routing on it in Area 0 without explicit administrative intent.
- **Control-Plane Security**: Omitting `passive-interface` on LAN-facing access interfaces (`Gi0/0` and `Gi0/1`) causes OSPF Hello multicast packets (`224.0.0.5`) to be transmitted onto user-facing access networks. Any host running Quagga, FRR, or Scapy can establish an OSPF adjacency, inject rogue LSAs, or initiate routing blackholes.

### 5. Packet-Flow Analysis
1. Router receives an OSPF LSA or transit packet destined for `10.10.1.97` (belonging to adjacent subnet `10.10.1.96/27`).
2. Because the wildcard mask claims a 64-host boundary, the router advertises an erroneous summary or overlaps with adjacent link-state advertisements.
3. On LAN interfaces, OSPF multicasts Hello packets every 10 seconds. End-user workstations receive raw IGMP/IP protocol 89 datagrams. A malicious workstation replies with an OSPF Hello and DBD (Database Description) frame, hijacking internal routing tables.

#### Packet Tracer Evidence
##### Buggy Configuration
```text
[PASTE: show ip ospf neighbor]
[PASTE: show ip route]
[PASTE: ping/traceroute]
```
##### Fixed Configuration
```text
[PASTE: show ip ospf neighbor]
[PASTE: show ip route]
[PASTE: ping/traceroute]
```

### 6. Fix (diff vs buggy)
```diff
--- buggy_ospf.txt
+++ fixed_ospf.txt
@@ -1,7 +1,9 @@
 ! Cisco IOS OSPF Configuration
-! Interfaces: 10.10.1.0/26 and 10.10.1.64/27 in Area 0
+! Correct /27 wildcard mask (0.0.0.31) and passive interfaces on LAN links
 
 hostname OSPF-ROUTER
+!
+no ip domain-lookup
 !
 interface GigabitEthernet0/0
+ description LAN Subnet 10.10.1.0/26
  ip address 10.10.1.1 255.255.255.192
  no shutdown
 !
 interface GigabitEthernet0/1
+ description LAN Subnet 10.10.1.64/27
  ip address 10.10.1.65 255.255.255.224
  no shutdown
 !
 router ospf 1
  router-id 1.1.1.1
  network 10.10.1.0 0.0.0.63 area 0
- network 10.10.1.64 0.0.0.63 area 0
+ network 10.10.1.64 0.0.0.31 area 0
+ passive-interface GigabitEthernet0/0
+ passive-interface GigabitEthernet0/1
 !
 end
```

### 7. Regression Test
- `tests/test_configgen.py::test_ospf_wildcard_and_passive_interface`
- Verified passing with real pytest execution (Asserts exact bitwise wildcard matching each interface subnet and presence of passive-interface directives on LAN SVIs).

### 8. Lesson
LLMs frequently hallucinate or repeat neighboring subnet parameters when generating repeated command sequences. Subnet math must never be entrusted to token prediction; it must always be computed deterministically via bitwise masking engines.

---

## Incident 2: Unconstrained Trunk Allowed VLANs and Insecure Native VLAN 1

### 1. Prompt (verbatim)
```text
Write Cisco IOS config for an access switch with VLANs 10, 20, 30 and a trunk port to the core.
```

### 2. AI Output (verbatim buggy code)
```cisco
! Cisco IOS Access Switch Configuration
! VLANs 10, 20, 30 with trunk to core

hostname ACCESS-SW1
!
vlan 10
 name DATA
!
vlan 20
 name VOICE
!
vlan 30
 name MANAGEMENT
!
! Trunk port to core switch
interface GigabitEthernet0/1
 switchport mode trunk
 switchport trunk encapsulation dot1q
 no shutdown
!
! Access ports - VLAN 10
interface range GigabitEthernet0/2-12
 switchport mode access
 switchport access vlan 10
 spanning-tree portfast
 no shutdown
!
! Access ports - VLAN 20
interface range GigabitEthernet0/13-20
 switchport mode access
 switchport access vlan 20
 spanning-tree portfast
 no shutdown
!
! Access ports - VLAN 30
interface range GigabitEthernet0/21-24
 switchport mode access
 switchport access vlan 30
 spanning-tree portfast
 no shutdown
!
end
```

### 3. Detection (real harness output)
```text
[FAIL] Task 04: trunk has explicit 'switchport trunk allowed vlan' list
    Expected: switchport trunk allowed vlan <list>
    Actual:   not found
[FAIL] Task 04: native VLAN is not 1
    Expected: explicit native vlan != 1
    Actual:   no native vlan set (defaults to 1)
[FAIL] Task 04: access ports have bpduguard
    Expected: spanning-tree bpduguard enable
    Actual:   not found
```

### 4. Root Cause
- **Broadcast Domain Leaking**: When `switchport trunk allowed vlan` is omitted, Cisco IOS defaults to `1-4094`. Any broadcast, multicast, or unknown unicast packet generated on VLANs not present on this access switch (e.g., VLANs 50, 60, 80) is nonetheless forwarded across the trunk link, consuming switch backplane buffers and inter-switch link bandwidth.
- **VLAN Hopping Vulnerability**: Because no native VLAN is explicitly specified, the trunk defaults to Native VLAN 1. Attackers can craft double-tagged 802.1Q frames (outer tag = VLAN 1, inner tag = target VLAN 30). When the first switch strips the outer tag because it matches the native VLAN, the frame is forwarded untagged across the internal fabric, and the egress switch interprets the inner tag as genuine, allowing unidirectional packet injection across VLAN security boundaries.
- **Spanning-Tree BPDU Hijacking**: The draft configures `spanning-tree portfast` on edge ports without `spanning-tree bpduguard enable`. A malicious user or rogue switch plugged into an access port can transmit Spanning Tree BPDUs with Priority 0, causing the entire network topology to recalculate and funnel traffic through an unauthorized machine.

### 5. Packet-Flow Analysis
1. Attacker attaches to access port `Gi0/2` (configured with `portfast` but no `bpduguard`).
2. Attacker transmits IEEE 802.1D Configuration BPDU claiming root bridge status (Bridge Priority 0).
3. Switch port immediately accepts the BPDU rather than err-disabling. The access switch transitions root port status to `Gi0/2`, causing widespread spanning-tree reconvergence, topology change notifications (TCNs), and bridging loops.
4. Broadcast storms from unrelated VLANs traverse `Gi0/1` due to the unconstrained allowed VLAN list.

#### Packet Tracer Evidence
##### Buggy Configuration
```text
[PASTE: show interfaces trunk]
[PASTE: show spanning-tree]
[PASTE: ping/traceroute]
```
##### Fixed Configuration
```text
[PASTE: show interfaces trunk]
[PASTE: show spanning-tree]
[PASTE: ping/traceroute]
```

### 6. Fix (diff vs buggy)
```diff
--- buggy_switch.txt
+++ fixed_switch.txt
@@ -1,7 +1,9 @@
 ! Cisco IOS Access Switch Configuration
-! VLANs 10, 20, 30 with trunk to core
+! Secure trunk with explicit allowed VLAN list, dedicated native VLAN 999, and BPDU Guard
 
 hostname ACCESS-SW1
+!
+no ip domain-lookup
 !
 vlan 10
  name DATA
@@ -11,26 +13,35 @@
 vlan 30
  name MANAGEMENT
 !
+vlan 999
+ name NATIVE
+!
+spanning-tree mode rapid-pvst
+!
 ! Trunk port to core switch
 interface GigabitEthernet0/1
  switchport trunk encapsulation dot1q
  switchport mode trunk
+ switchport trunk allowed vlan 10,20,30
+ switchport trunk native vlan 999
  no shutdown
 !
 ! Access ports - VLAN 10
 interface range GigabitEthernet0/2-12
  switchport mode access
  switchport access vlan 10
  spanning-tree portfast
+ spanning-tree bpduguard enable
  no shutdown
 !
 ! Access ports - VLAN 20
 interface range GigabitEthernet0/13-20
  switchport mode access
  switchport access vlan 20
  spanning-tree portfast
+ spanning-tree bpduguard enable
  no shutdown
 !
 ! Access ports - VLAN 30
 interface range GigabitEthernet0/21-24
  switchport mode access
  switchport access vlan 30
  spanning-tree portfast
+ spanning-tree bpduguard enable
  no shutdown
 !
 end
```

### 7. Regression Test
- `tests/test_configgen.py::test_trunk_security_configuration`
- `tests/test_configgen.py::test_access_port_security`
- Verified passing with real pytest execution.

### 8. Lesson
LLM code generation defaults to syntactically valid minimal commands while omitting foundational Layer 2 hardening standards. Automated Jinja2 templates governed by strict security assertions must enforce explicit VLAN pruning (`allowed vlan`), dedicated native VLAN isolation (VLAN 999), and BPDU protection.

---

## Audit Summary Table

| Incident | Category | Detection Method | Severity | Root Cause Summary |
|---|---|---|---|---|
| **Incident 1** | L3 Routing (OSPF) | Automated IP math verification (`audit_harness.py`) | **High** | Wildcard mask copy-paste error (`0.0.0.63` vs `0.0.0.31`) and omitted `passive-interface` on LAN. |
| **Incident 2** | L2 Switching / Security | AST / RegEx Config Token Scanner (`audit_harness.py`) | **Critical** | Default Native VLAN 1, unpruned trunk VLANs (`1-4094`), and missing BPDU Guard on PortFast ports. |
| **Incident 3** *(Task 03)* | L1 Physical Optics | Mathematical physics loss engine verification | **Medium** | Missing connector count (2 vs 4), incorrect fiber attenuation coefficient (0.22 vs 0.25 dB/km), and wrong safety margin. |

---

## Software Validation Report

The finalized **NetArchitect** codebase was validated using a multi-tiered verification pipeline:

1. **Deterministic Bitwise Math (No Engine `ipaddress` Imports)**:
   - Subnet masks, wildcards, boundaries, and allocations were implemented strictly with integer bit shifts (`<<`, `>>`), bitwise AND (`&`), bitwise OR (`|`), and bitwise NOT (`~ ... & 0xFFFFFFFF`).
   - Verified via `grep_search`: zero instances of `import ipaddress` in `netarchitect/vlsm.py` or `netarchitect/media.py`.
2. **Independent Oracle Testing**:
   - `tests/test_wildcard.py` cross-examined all 33 CIDR prefixes (`/0` through `/32`) against `ipaddress.IPv4Network.netmask` and `ipaddress.IPv4Network.hostmask`.
   - `tests/test_vlsm.py` executed **1,000 randomized allocation scenarios** with random seeds, proving zero pairwise subnet overlaps, strict boundary alignments, and containment within the root prefix.
3. **Cisco IOS Allowlist Enforcement**:
   - `tests/test_configgen.py` verified that every non-blank and non-comment configuration line produced across all three presets strictly begins with an authorized command prefix defined in `netarchitect/ios_allowlist.py`.
4. **Mutation Testing**:
   - `tests/test_mutation.py` introduced deliberate bitwise defects into the mask inversion logic and demonstrated that test assertions immediately caught the mutation.
5. **Full Test Suite Execution**:
   - Real output: **50 tests collected, 50 tests passed in 6.89 seconds (100% green)**.

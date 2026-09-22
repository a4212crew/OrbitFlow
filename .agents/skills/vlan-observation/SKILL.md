---
name: vlan-observation
description: Use for read-only multi-vendor VLAN observation in OrbitFlow, including per-interface VLAN references, VLAN database/equivalent service objects, normalization, and vendor adapter boundaries. Consistency/policy checking is explicitly out of scope.
---

# VLAN Observation Capability

## Purpose

Build one reusable read-only capability that answers:

1. What VLANs are configured or referenced on each interface?
2. What VLANs exist in the device VLAN database or equivalent service construct?

Vendor parsers report observed facts only. A separate analysis/policy layer will later decide whether those facts are consistent or compliant.

## Architecture Rules

- Consume a resolved DeviceContext/platform from the device-inventory layer when orchestration starts from only an IP; do not implement independent platform discovery here.
- Reuse `connect_device(...)` / `DeviceSession`; do not create new transport logic.
- Keep vendor commands/parsers isolated.
- Normalize into common structured VLAN state.
- Do not infer unsupported values.
- Do not treat absence from a traditional VLAN database as an error when the platform/service model does not require one.
- Keep observation separate from consistency analysis, planning, apply, and verification.
- Do not add or change device commands without explicit operator approval.

## Initial Approved Collection Commands

Cisco IOS / IOS-XE:

```text
show running-config
```

Huawei VRP / NE05E:

```text
display current-configuration
```

Ubiquiti EdgeSwitch:

```text
show running-config
```

Cisco IOS-XR command selection is not yet approved for this capability. Inspect the current repository and discuss the smallest appropriate read-only running-configuration command before implementation.

## Normalized Intent

The model should be able to represent, where applicable:

- device name, device IP, platform;
- VLAN database/equivalent objects;
- interface name and description;
- mode: access, hybrid, trunk, service, routed_subinterface, svi, unknown;
- access VLAN, native VLAN, PVID;
- tagged, untagged, and allowed VLANs;
- service VLAN, outer VLAN, inner VLAN;
- referenced VLANs;
- VLAN source/construct;
- whether a traditional VLAN-database membership check is applicable;
- service binding type/name when relevant.

Not every field applies to every platform.

## Vendor Semantics

### Cisco IOS — 3750X

Parse classic switchport configuration from `show running-config`.

Access example:

```text
switchport access vlan 445
switchport mode access
```

Trunk example:

```text
switchport trunk encapsulation dot1q
switchport mode trunk
switchport trunk allowed vlan ...
switchport trunk native vlan ...
```

Global VLAN database is represented by `vlan <id>` sections.

If `switchport trunk allowed vlan` is absent, record that the allowed list is not explicitly configured; do not manufacture an explicit VLAN list.

Login/MOTD banners may contain `#`. Do not weaken existing stable-prompt and command-echo synchronization.

### Cisco IOS-XE — ASR920 / ME3600X

Support both classic switchport syntax and EVC/service-instance constructs.

Typical EVC facts include:

```text
service instance <id> ethernet
 encapsulation dot1q <vlan>
 bridge-domain <id>
```

Do not force EVC/service-instance state into the classic switchport model. Preserve VLAN encapsulation and bridge-domain/service relationships separately.

### Cisco IOS-XR — NCS540

Treat VLANs as service/subinterface constructs rather than assuming a traditional VLAN database. Relevant concepts may include dot1q/QinQ encapsulation, `l2transport`, and L2VPN bridge-domain/service association.

Do not report a missing traditional VLAN database as an inconsistency when that database concept is not applicable.

### Huawei VRP — NE05E

Traditional switched VLANs are database-backed.

Examples:

```text
vlan batch 545 745 to 746

port link-type access
port default vlan 545

port link-type trunk
port trunk allow-pass vlan 545 745
```

For these constructs, VLAN database presence is relevant.

Service/routed subinterfaces are different:

```text
vlan-type dot1q 1376
```

or:

```text
control-vid 445 dot1q-termination
dot1q termination vid 445
l2 binding vsi LBB-PPPOE-2445
```

These VLANs are valid interface/service VLANs even when absent from `vlan batch`. Do not require database membership for `vlan-type dot1q` or `dot1q termination vid`.

Capture `VlanifX` appropriately. VSI identity is separate from VLAN identity; never assume a VSI ID/name equals the VLAN ID.

### Ubiquiti EdgeSwitch

Global database example:

```text
vlan database
vlan 445,545,745,1101,2400-2444,2449,4000-4001
```

Interface facts come from:

```text
vlan pvid <vlan>
vlan participation include <vlans>
vlan participation exclude <vlans>
vlan tagging <vlans>
```

Confirmed customer/hybrid pattern:

```text
vlan pvid 445
vlan participation include 445,1101
vlan tagging 1101
```

Interpret 445 as PVID/untagged, 1101 as tagged, and both as referenced VLANs.

A port where the participating service VLAN set is tagged should be represented as a trunk/service transport pattern as appropriate.

## Future Consistency Layer

The future checker should consume normalized state rather than raw vendor configuration.

Conceptually:

```text
for each interface:
    for each referenced VLAN:
        if a VLAN-database check is applicable:
            compare against the observed VLAN database
        else:
            retain the service VLAN as valid observed state
```

Do not implement that policy/compliance checker as part of the observation capability unless explicitly requested.

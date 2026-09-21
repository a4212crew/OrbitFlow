---
name: ubiquiti-network-cli
description: Use for Ubiquiti EdgeSwitch CLI behaviour in OrbitFlow, including interface collection, access VLAN/PVID configuration, verification, firmware caveats, and EdgeSwitch-specific parsing.
---

# Ubiquiti EdgeSwitch CLI

## Use This Skill When

Use for EdgeSwitch-specific commands, parsing, configuration generation, or verification.

Also use:
- `../interface-collector/SKILL.md`
- `../vlan-observation/SKILL.md`
- `../access-vlan-provisioning/SKILL.md`

Do not add UISP API behaviour to this skill unless a future explicit task expands scope.

## Interface Collection

Primary baseline:

```text
terminal length 0
show interfaces status all
```

Do not use `show interfaces description` or guess a fallback command.

Mapping guidance:
- interface `Name`, if present -> Port Description;
- link state/status -> Oper Status;
- if admin status is not clearly available, use empty/`unknown`; do not guess.

## Access VLAN Baseline

Conceptual candidate:

```text
configure
interface <Port Name>
description "<Description>"
vlan pvid <VLAN>
vlan participation include <VLAN>
vlan tagging <VLAN> disable
exit
write memory
```

Pre/post checks may include:

```text
show running-config interface <Port Name>
show interfaces status all
show vlan
```

Verification should confirm interface existence, matching description, requested PVID, VLAN participation, and untagged/access state.

## Firmware Caveat

EdgeSwitch syntax may vary by firmware.

If an expected command is rejected, capture failure and stop that row. Do not guess alternate syntax unless the platform profile/task explicitly defines it.

Rollback must use captured pre-change configuration; do not guess previous state.


## VLAN Observation

Approved read-only configuration source:

```text
show running-config
```

Parse the global `vlan database` section and VLAN lists/ranges.

Per-interface VLAN facts may include:
- `vlan pvid <id>`;
- `vlan participation include <vlans>`;
- `vlan participation exclude <vlans>`;
- `vlan tagging <vlans>`.

Confirmed customer/hybrid example:

```text
vlan pvid 445
vlan participation include 445,1101
vlan tagging 1101
```

Interpret VLAN 445 as PVID/untagged, VLAN 1101 as tagged, and both as referenced VLANs.

A trunk/uplink may participate in and tag the same broad VLAN set. Preserve observed membership/tagging facts and let the later analysis layer decide consistency.

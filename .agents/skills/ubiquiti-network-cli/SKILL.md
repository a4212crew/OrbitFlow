---
name: ubiquiti-network-cli
description: Use for Ubiquiti EdgeSwitch CLI behaviour in OrbitFlow, including interface collection, access VLAN/PVID configuration, verification, firmware caveats, and EdgeSwitch-specific parsing.
---

# Ubiquiti EdgeSwitch CLI

## Use This Skill When

Use for EdgeSwitch-specific commands, parsing, configuration generation, or verification.

Also use:
- `../interface-collector/SKILL.md`
- `../access-vlan-provisioning/SKILL.md`

Do not add UISP API behaviour to this skill unless a future explicit task expands scope.

## Interface Collection

Primary baseline:

```text
show interfaces status
```

Optional fallback where firmware supports it:

```text
show interfaces description
```

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
show interfaces status
show vlan
```

Verification should confirm interface existence, matching description, requested PVID, VLAN participation, and untagged/access state.

## Firmware Caveat

EdgeSwitch syntax may vary by firmware.

If an expected command is rejected, capture failure and stop that row. Do not guess alternate syntax unless the platform profile/task explicitly defines it.

Rollback must use captured pre-change configuration; do not guess previous state.

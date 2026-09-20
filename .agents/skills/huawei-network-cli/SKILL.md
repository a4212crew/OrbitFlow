---
name: huawei-network-cli
description: Use for Huawei VRP behaviour in OrbitFlow, including NE05/NE05E interface collection, access VLAN or dot1q subinterface configuration, verification, and Huawei-specific caveats.
---

# Huawei Network CLI

## Use This Skill When

Use for Huawei VRP-specific commands, parsing assumptions, configuration generation, or verification.

Also use:
- `../interface-collector/SKILL.md`
- `../access-vlan-provisioning/SKILL.md`

Do not implement Teleport transport here.

## Platform

Primary current family:
- Huawei VRP
- NE05 / NE05E

## Interface Collection

Baseline commands:

```text
display interface brief
display interface description
```

Use whichever command(s) the collector profile defines for required fields, and normalize into the common collector record.

## Physical Access VLAN Baseline

Use only when the explicit service/platform profile supports physical access mode.

```text
system-view
interface <Port Name>
 description <Description>
 port link-type access
 port default vlan <VLAN>
 undo shutdown
quit
save
```

## Dot1q Subinterface Baseline

Use only when the requested workflow/platform profile explicitly requires it.

```text
system-view
interface <Port Name>.<VLAN>
 description <Description>
 vlan-type dot1q <VLAN>
quit
save
```

## Checks

Pre/post checks may include:

```text
display current-configuration interface <Port Name>
display interface description | include <Port Name>
display vlan <VLAN>
```

Verification should confirm interface/service existence, matching description, requested VLAN mode/encapsulation, and command acceptance.

## Safety Caveats

- Do not assume every NE05E port is safe for physical access mode.
- Do not silently switch to QinQ or L2VPN service models.
- Future QinQ/L2VPN models must be explicit actions.
- Rollback must rely on captured pre-change configuration; never guess previous VLAN state.

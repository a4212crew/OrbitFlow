---
name: cisco-network-cli
description: Use for Cisco IOS, IOS-XE, or IOS-XR behaviour in OrbitFlow, including interface collection, paging, access VLAN configuration, IOS-XR L2 subinterfaces, pre/post checks, commits, verification, and Cisco-specific caveats.
---

# Cisco Network CLI

## Use This Skill When

Use when a task changes Cisco-specific commands, configuration generation, verification, parsing assumptions, paging, or platform behaviour.

Also use the relevant task skill:
- interface collection -> `../interface-collector/SKILL.md`
- VLAN observation -> `../vlan-observation/SKILL.md`
- access VLAN provisioning -> `../access-vlan-provisioning/SKILL.md`

Do not implement Teleport transport here.

## Supported Families

- Cisco IOS
- Cisco IOS-XE
- Cisco IOS-XR

Keep IOS/IOS-XE and IOS-XR behaviour separate.

## Interactive CLI

IOS/IOS-XE baseline paging disable:

```text
terminal length 0
```

Prompt detection should remain dynamic rather than hostname-specific.

## Interface Collection

Baseline:

```text
show interfaces description
```

Normalize platform output through collector logic.

## IOS / IOS-XE — Access VLAN Baseline

Use only where the interface/service model supports classic switchport access mode.

Conceptual candidate:

```text
configure terminal
interface <Port Name>
 description <Description>
 switchport
 switchport mode access
 switchport access vlan <VLAN>
 no shutdown
end
write memory
```

Pre/post checks may include:

```text
show running-config interface <Port Name>
show interfaces description | include <Port Name>
show interfaces switchport <Port Name>
show vlan id <VLAN>
```

Verification should confirm interface existence, description, access VLAN, appropriate administrative state, and command acceptance.

### Important IOS/IOS-XE Caveat

ASR920 or ME3600X services may use EVC/service-instance models rather than classic switchport access mode.

Do not assume every Ethernet interface supports `switchport`.

If the model is rejected, record failure. Do not guess another service model unless the task explicitly defines it.

## IOS-XR — L2 Subinterface Baseline

IOS-XR does not use classic IOS `switchport access vlan` syntax.

Conceptual L2 subinterface candidate:

```text
configure terminal
interface <Port Name>.<VLAN> l2transport
 description <Description>
 encapsulation dot1q <VLAN>
 no shutdown
commit
end
```

Pre/post checks may include:

```text
show running-config interface <Port Name>
show running-config interface <Port Name>.<VLAN>
show interfaces description | include <Port Name>
show interfaces <Port Name>.<VLAN>
```

Verification should confirm subinterface existence, dot1q encapsulation, description, successful commit, and appropriate interface state.

Store commit output in audit evidence.

Rollback should rely on captured pre-change state and explicit rollback logic, not guesses.

## Mapping Principle

Keep OrbitFlow platform identifiers separate from library-specific driver identifiers.

Do not assume `cisco_ios`, `cisco_xe`, and `cisco_xr` are interchangeable merely because a command happens to match.


## VLAN Observation

Approved read-only configuration source for Cisco IOS / IOS-XE:

```text
show running-config
```

### IOS / 3750X

Parse global `vlan <id>` sections as the traditional VLAN database.

Parse classic access/trunk interface facts including:
- `switchport mode access`
- `switchport access vlan <id>`
- `switchport mode trunk`
- optional `switchport trunk allowed vlan ...`
- optional `switchport trunk native vlan ...`

If an explicit trunk allowed list is absent, record it as not explicitly configured rather than inventing an explicit list.

Login/MOTD banners may themselves contain `#`; preserve the existing stable dynamic-prompt and command-echo synchronization behavior.

### IOS-XE / ASR920 / ME3600X

In addition to classic switchport syntax, support EVC/service-instance observations such as `service instance <id> ethernet`, `encapsulation dot1q <vlan>`, and `bridge-domain <id>`.

Keep encapsulation VLAN and bridge-domain/service identity separate; do not force EVC state into the classic switchport model.

### IOS-XR / NCS540

Treat VLANs as service/subinterface constructs rather than assuming a classic VLAN database. The VLAN-observation collection command for IOS-XR is not yet approved; discuss it before implementation.

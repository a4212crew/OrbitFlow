---
name: cisco-network-cli
description: Use for Cisco IOS, IOS-XE, or IOS-XR behaviour in OrbitFlow, including interface collection, paging, access VLAN configuration, IOS-XR L2 subinterfaces, pre/post checks, commits, verification, and Cisco-specific caveats.
---

# Cisco Network CLI

## Use This Skill When

Use when a task changes Cisco-specific commands, configuration generation, verification, parsing assumptions, paging, or platform behaviour.

Also use the relevant task skill:
- interface collection -> `../interface-collector/SKILL.md`
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

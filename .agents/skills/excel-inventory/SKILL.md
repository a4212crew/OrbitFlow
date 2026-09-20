---
name: excel-inventory
description: Use for OrbitFlow Excel inventory loading, device target input, required columns, platform normalization, credential precedence, inventory validation, Location ID handling, or inventory tests.
---

# Excel Inventory

## Use This Skill When

Use for inventory workbook loading, required/optional fields, row validation, platform normalization, device target selection, credential precedence related to inventory, Location ID handling, and inventory tests.

Do not use this skill for Teleport transport implementation, interface parsing, or access VLAN command generation.

## Related Skills

- `../jumphost-connectivity/SKILL.md` for device connection transport.
- `../interface-collector/SKILL.md` for collection.
- `../access-vlan-provisioning/SKILL.md` for provisioning input.

## Principle

Inventory is the source of truth for device targets. Do not hardcode production device lists into task workflows.

## Core Device Inventory Fields

| Column | Purpose | Requirement |
|---|---|---|
| `Device Name` | Hostname/friendly name | Required |
| `Device IP` | Management address | Required |
| `Platform` | OrbitFlow platform identifier | Required |
| `Username` | Device login | Optional if credential provider supplies it |
| `Password` | Device password | Optional if credential provider supplies it |
| `Secret` | Enable secret where required | Optional |
| `Port` | SSH port | Optional, default 22 |

Keep column names centralized as constants where practical.

## Security

Preferred behaviour:
1. approved credential provider / environment / secret store;
2. inventory credentials only where explicit compatibility requires them;
3. never print or log credential values.

Do not require passwords to be stored in Excel.

## Validation

At minimum:
- required columns exist;
- inventory is not empty when a device operation is requested;
- target address is present;
- platform normalizes to a supported identifier;
- optional port is valid when supplied;
- invalid rows produce clear row-specific errors.

A bad row must not terminate an otherwise safe multi-device batch.

## Platform Identifiers

Current intended identifiers:
- `cisco_ios`
- `cisco_xe`
- `cisco_xr`
- `huawei_vrp`
- `ubiquiti_edgeswitch`

Keep OrbitFlow platform identifiers separate from library-specific driver names where needed.

## Location ID

Where workflows use Location ID, preserve the project convention that it starts with `LW` and ends at the last consecutive digit in that ID token. Do not invent a Location ID when none is present.

## Testing

Unit tests should cover:
- valid inventory load;
- missing required columns;
- empty inventory;
- unsupported platform;
- malformed optional values;
- platform/Location ID normalization;
- credential values not appearing in logs/errors.

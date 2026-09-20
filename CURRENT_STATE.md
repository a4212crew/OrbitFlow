# CURRENT_STATE.md — OrbitFlow Current State

Use this file as the concise source of truth for what is implemented and validated today.

Keep this document short. Historical implementation detail belongs in `docs/devlog/YYYY-MM.md`.

## Project

OrbitFlow is a multi-vendor ISP network automation platform designed to scale toward approximately 1,500 network devices.

Core rules and skill routing are defined in `AGENTS.md`.

## Architectural Direction

OrbitFlow is being developed as a reusable network-equipment capability platform and future OSS layer.

The intended dependency flow is:

```text
External OSS/BSS / REST API / GUI / schedulers
        -> Integration layer
        -> Application / workflow layer
        -> Reusable device capability layer
        -> Vendor-specific implementation
        -> DeviceSession / transport
        -> Network equipment
```

Key rules:
- implement each network-device capability once;
- vendor-specific command/parsing logic remains isolated;
- normalize CLI output into reusable structured models;
- workflows compose capabilities for audit, troubleshooting, provisioning, remediation, service assurance, and similar functions;
- REST/API consumers must call the same application/capability interfaces as internal workflows;
- separate observe -> analyze -> plan -> apply -> verify -> record;
- do not make raw CLI execution the primary external OSS interface.

Detailed model: `docs/architecture/device-capability-oss-model.md`.

## Current Architecture

### Transport

All network-device access uses the shared OrbitFlow transport layer.

**Windows**
- Validated Teleport local-port-forward model using `tsh ssh -N -L`.
- Tunnel startup retries local-forward connections within `connect_timeout`.
- The first connected local-forward socket is retained and passed directly to
  Paramiko; OrbitFlow does not read or consume the device's SSH banner.
- Live validated successfully.

**Linux / Ubuntu**
- Validated `tsh proxy ssh` + Teleport private key/certificate + Paramiko `direct-tcpip` model.
- A second Paramiko session connects to the target device through the bastion channel.
- Live validated successfully.

Both target-device paths first use normal Paramiko authentication. If password
authentication is rejected, the shared target authenticator retries with
keyboard-interactive authentication using the same `DeviceCredentials.password`.
It responds only to prompts explicitly identified as password prompts. This
fallback does not affect Teleport/bastion authentication.

Higher-level workflows must use `connect_device(...)` / `DeviceSession` and must not recreate OS-specific transport.

### SSH Host-Key Behaviour

Current deployment defaults:
- `verify_bastion_host_key=False`
- `verify_device_host_key=False`

Permissive mode uses Paramiko `AutoAddPolicy` without persisting learned keys.

Strict verification remains configurable for future use. Custom Teleport CA verification is not implemented.

### Interactive CLI and Interface Capability

Implemented reusable `CiscoIOSCLI` above `DeviceSession`.

Current behaviour:
- dynamic prompt detection for prompts ending in `#` or `>`;
- automatic `terminal length 0`;
- timeout-aware prompt reads using monotonic deadlines;
- command-echo synchronization to prevent stale prompts from completing a newly sent command;
- command echo removal;
- ANSI/control-sequence cleanup;
- trailing prompt removal;
- prompt changes tracked dynamically.

Windows live-device validation passed against Cisco ASR920 `NSW-STLEON-21CANB-BAS1` running IOS XE 17.06.07. The validation confirmed correct prompt detection, paging disablement, complete `show version` output, clean output handling, stale-prompt fix, and clean session teardown.

Implemented one reusable `InterfaceService` and normalized `InterfaceRecord` for
Cisco IOS, IOS-XE, IOS-XR, Huawei VRP / NE05E, and Ubiquiti EdgeSwitch. Each
platform has an isolated command/parser adapter, uses `DeviceSession`, disables
paging with the approved platform command, and returns a clear error for a
rejected setup or collection command. Empty command output produces an empty
collection; unrecognized non-empty output is a parser failure. The capability
does not guess fallback commands after a rejection. Huawei accepts both the
status-bearing and description-only forms of `display interface description`;
for the description-only form it uses the approved `display interface brief`
fallback and joins status by Huawei-canonical interface name (`Eth`/`Ethernet`,
`GE`/`GigabitEthernet`, `Loop`/`LoopBack`, and `Tun`/`Tunnel`), while preserving
the description-side name and subinterface suffix in normalized output. Known VRP
brief legends and protocol
suffixes such as `up(s)` are accepted; PHY remains authoritative for normalized
status. The
IOS-XR parser accepts
the platform's timestamp line before the interface table while remaining strict
about other unexpected content. `device_name` is optional:
vendor adapters extract it from their already-detected CLI prompt, while an
explicit caller-supplied name remains a compatibility override.
EdgeSwitch uses only `terminal length 0` and `show interfaces status all`; its
parser supports the confirmed multi-line status header, blank names, short
rows, and `(hostname) #` prompts while leaving unavailable admin state empty.

`scripts/live_validate_interfaces.py` provides a deliberately limited
single-device integration entry point for live validation of this existing
capability. It accepts caller-supplied credentials and `TransportConfig`, prints
normalized records, and does not implement inventory or production collection.

## Repository Structure

Current major implementation areas:
- `src/orbitflow/transport/` — shared and OS-specific transport;
- `src/orbitflow/vendors/cisco/` — Cisco IOS/IOS-XE CLI behaviour;
- `src/orbitflow/vendors/huawei/` and `src/orbitflow/vendors/ubiquiti/` — vendor interface collection/parsing;
- `src/orbitflow/capabilities/` and `src/orbitflow/models.py` — reusable capabilities and normalized records;
- `scripts/live_validate_interfaces.py` — single-device interface integration validation;
- `tests/` — deterministic mocked/unit tests;
- `.agents/skills/` — task/vendor-specific implementation guidance.

## Validation Baseline

- Windows transport: live validated.
- Linux transport: live validated.
- Cisco IOS/IOS-XE interactive CLI on Windows: live validated.
- Current automated test suite includes transport and Cisco CLI regression coverage.
- Interface capability tests cover all five platform identifiers with deterministic fake sessions.

## Known Limitations

- Current SSH host-key defaults are permissive and therefore do not provide MITM protection.
- Inventory and production collection workflows are not yet implemented.
- Interface collection has not been end-to-end live validated by the automated
  suite on IOS-XR, Huawei, or EdgeSwitch; EdgeSwitch parsing is covered against
  confirmed captured live output, and untested output variants fail clearly
  instead of being guessed.
- Live-device testing is integration validation and does not replace deterministic unit tests.

## Current Development Focus

Build inventory-driven collection, change tracking, and reporting on top of the reusable interface capability without duplicating its vendor logic.

Expected flow:

```text
Inventory
  -> connect_device / DeviceSession
  -> reusable interface capability
  -> vendor CLI + vendor parser
  -> normalized interface records
  -> workflow analysis / change tracking
  -> reporting
  -> future REST/API exposure through the same capability/service interface
```

Relevant skills:
- `.agents/skills/interface-collector/SKILL.md`
- `.agents/skills/excel-inventory/SKILL.md`
- `.agents/skills/cisco-network-cli/SKILL.md`

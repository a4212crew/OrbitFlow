# CURRENT_STATE.md — OrbitFlow Current State

Use this file as the concise source of truth for what is implemented and validated today.

Keep this document short. Historical implementation detail belongs in `docs/devlog/YYYY-MM.md`.

## Project

OrbitFlow is a multi-vendor ISP network automation platform designed to scale toward approximately 1,500 network devices.

Core rules and skill routing are defined in `AGENTS.md`.

## Current Architecture

### Transport

All network-device access uses the shared OrbitFlow transport layer.

**Windows**
- Validated Teleport local-port-forward model using `tsh ssh -N -L`.
- Paramiko connects to the target device through the local forward.
- Live validated successfully.

**Linux / Ubuntu**
- Validated `tsh proxy ssh` + Teleport private key/certificate + Paramiko `direct-tcpip` model.
- A second Paramiko session connects to the target device through the bastion channel.
- Live validated successfully.

Higher-level workflows must use `connect_device(...)` / `DeviceSession` and must not recreate OS-specific transport.

### SSH Host-Key Behaviour

Current deployment defaults:
- `verify_bastion_host_key=False`
- `verify_device_host_key=False`

Permissive mode uses Paramiko `AutoAddPolicy` without persisting learned keys.

Strict verification remains configurable for future use. Custom Teleport CA verification is not implemented.

### Cisco IOS / IOS-XE CLI

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

IOS-XR requires a separate future implementation.

## Repository Structure

Current major implementation areas:
- `src/orbitflow/transport/` — shared and OS-specific transport;
- `src/orbitflow/vendors/cisco/` — Cisco IOS/IOS-XE CLI behaviour;
- `tests/` — deterministic mocked/unit tests;
- `.agents/skills/` — task/vendor-specific implementation guidance.

## Validation Baseline

- Windows transport: live validated.
- Linux transport: live validated.
- Cisco IOS/IOS-XE interactive CLI on Windows: live validated.
- Current automated test suite includes transport and Cisco CLI regression coverage.

## Known Limitations

- Current SSH host-key defaults are permissive and therefore do not provide MITM protection.
- Cisco IOS-XR CLI support is not implemented.
- Inventory and production collection workflows are not yet implemented.
- Live-device testing is integration validation and does not replace deterministic unit tests.

## Current Development Focus

Build the interface-description collector on top of the existing transport and Cisco IOS/IOS-XE CLI layers.

Expected flow:

```text
Inventory
  -> connect_device / DeviceSession
  -> vendor CLI
  -> show interfaces description
  -> vendor parser
  -> normalized records
  -> change tracking / reporting
```

Relevant skills:
- `.agents/skills/interface-collector/SKILL.md`
- `.agents/skills/excel-inventory/SKILL.md`
- `.agents/skills/cisco-network-cli/SKILL.md`

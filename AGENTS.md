# AGENTS.md — OrbitFlow Network Automation

## 1. Project Purpose

OrbitFlow is a multi-vendor network automation platform for ISP operations.

OrbitFlow may perform inventory-driven device access, interface/operational data collection, deterministic parsing and normalization, controlled provisioning, verification, Excel-based reporting, audit, and change tracking.

Design for approximately 1,500 network devices without assuming all devices behave identically.

## 2. Core Operating Principles

1. **Inventory is the source of truth for device targets.** Do not hardcode production device lists into workflow code.
2. **Vendor-specific behaviour must remain isolated.** Cisco IOS, IOS-XE, IOS-XR, Huawei VRP, and Ubiquiti EdgeSwitch are not one generic CLI platform.
3. **Use deterministic runtime behaviour.** Runtime configuration generation must use explicit logic/templates; do not use an LLM at runtime to invent network configuration.
4. **Isolate operational failures.** One failed device or input row must not terminate a batch unless continuing would create a safety risk.
5. **Protect credentials and secrets.** Never log passwords, OTPs, private keys, tokens, or full secret-bearing environment dumps. Do not commit real credentials.
6. **Preserve working behaviour.** Do not silently redesign validated architecture or change behaviour outside the requested task scope.

## 3. Supported Network Platforms

Current intended platform families:
- Cisco IOS
- Cisco IOS-XE
- Cisco IOS-XR
- Huawei VRP
- Ubiquiti EdgeSwitch

Keep platform mapping configurable.

## 4. Repository Architecture Principles

Keep the codebase modular. Separate:
- transport and jumphost connectivity;
- inventory/input handling;
- task workflows;
- vendor-specific CLI behaviour;
- parsers and normalization;
- output/reporting;
- configuration generation and verification;
- tests.

Avoid large monolithic scripts when a reusable module boundary is practical.

Higher-level workflows must not implement their own independent SSH/jumphost logic.

## 5. Transport Architecture

All network-device access must use the approved OrbitFlow transport layer.

### Windows
Use the validated Teleport local-port-forward model.

### Linux / Ubuntu
Use the validated `tsh proxy ssh` + Teleport certificate + Paramiko `direct-tcpip` model.

Collector, provisioning, parser, and reporting modules must not recreate OS-specific transport logic.

Higher-level code should request a device session without needing to know whether the execution host is Windows or Linux.

For implementation details, load:

`.agents/skills/jumphost-connectivity/SKILL.md`

## 6. Inventory Principle

Excel inventory is the primary device-target input unless an explicit future task introduces another approved inventory source.

Inventory handling must validate required fields, normalize platform identifiers, keep credentials separate from normal inventory data where practical, and fail clearly on invalid input.

For detailed inventory rules, load:

`.agents/skills/excel-inventory/SKILL.md`

## 7. Collection Principle

Collection workflows must acquire sessions through the OrbitFlow transport layer, use vendor-aware commands/parsing, normalize results into common records, isolate per-device failures, preserve tracking history, scale toward approximately 1,500 devices, and have tests for deterministic logic.

For interface collection work, load:

`.agents/skills/interface-collector/SKILL.md`

## 8. Provisioning Safety Principles

Configuration-changing workflows are high-safety operational features.

Rules:
1. Read-only operations may run normally.
2. Configuration changes must be explicitly requested.
3. Default behaviour must be non-destructive.
4. Follow `validate -> pre-check -> generate -> apply -> verify -> record`.
5. Capture pre-change evidence before applying configuration.
6. Generate rollback evidence/candidates where appropriate.
7. Do not automatically execute rollback unless an explicit rollback workflow exists.
8. Use deterministic vendor-specific configuration generation.
9. Failure on one provisioning row must not crash the entire batch unless continuing would be unsafe.
10. Never expose credentials in provisioning logs or output workbooks.

For access VLAN provisioning, load:

`.agents/skills/access-vlan-provisioning/SKILL.md`

## 9. Scalability, Logging, and Testing

### Scalability
- Design batch operations for approximately 1,500 devices.
- Use bounded concurrency where appropriate.
- Do not repeatedly write the final Excel workbook per device during large runs.
- Isolate per-device exceptions.

### Logging
- Operational workflows must produce useful logs.
- Logs must identify affected device/task context without exposing credentials.
- Keep logging behaviour centralized where practical.

### Testing
- Unit-test deterministic logic without requiring live network devices.
- Live-device testing is appropriate for transport and integration validation.
- Add/update tests when changing parsing, normalization, comparison, configuration generation, validation, verification, or Excel-writing logic.
- A task is not complete until relevant tests/acceptance criteria pass, or an untested limitation is stated explicitly.

## 10. Skill Routing

Do **not** read every skill by default.

Read only:
1. the skill directly relevant to the task;
2. any related skill explicitly referenced by that skill;
3. the vendor-specific skill for the affected platform when vendor behaviour is involved.

| Task | Skill |
|---|---|
| Teleport, jumphost, SSH transport, Paramiko transport | `.agents/skills/jumphost-connectivity/SKILL.md` |
| Excel inventory input, validation, credential precedence | `.agents/skills/excel-inventory/SKILL.md` |
| Interface description/status collection, parsing, change tracking | `.agents/skills/interface-collector/SKILL.md` |
| Access VLAN provisioning, dry-run/apply/verify, rollback evidence | `.agents/skills/access-vlan-provisioning/SKILL.md` |
| Cisco IOS / IOS-XE / IOS-XR CLI behaviour | `.agents/skills/cisco-network-cli/SKILL.md` |
| Huawei VRP CLI behaviour | `.agents/skills/huawei-network-cli/SKILL.md` |
| Ubiquiti EdgeSwitch CLI behaviour | `.agents/skills/ubiquiti-network-cli/SKILL.md` |

## 11. Codex Working Rules

When modifying this repository:

1. Read this `AGENTS.md` first.
2. Identify the relevant skill(s); do not load every skill unnecessarily.
3. Preserve the validated transport architecture.
4. Do not bypass provisioning safety rules.
5. Do not log or hardcode credentials.
6. Keep vendor-specific behaviour isolated.
7. Preserve existing working behaviour unless the task explicitly changes it.
8. Add or update tests for changed deterministic logic.
9. Keep existing CLI behaviour stable unless the task explicitly changes it.
10. Update `DEVLOG.md` after completing a meaningful task.
11. Do not silently redesign architecture outside the requested scope.
12. If a requested change conflicts with these rules, surface the conflict before implementing it.

## 12. Documentation Responsibilities

- `AGENTS.md` — permanent architectural rules and skill routing.
- `.agents/skills/*/SKILL.md` — task-specific or vendor-specific implementation knowledge.
- `DEVLOG.md` — completed work, decisions, tests, known issues, and follow-up items.
- `ROADMAP.md` — future work and enhancement ideas.
- `README.md` — operator/developer setup and usage.
- dependency files — actual package requirements.

When CLI usage, setup, dependencies, or operational behaviour changes, update the appropriate documentation instead of expanding `AGENTS.md` with task-specific detail.

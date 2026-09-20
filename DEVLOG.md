# DEVLOG.md — OrbitFlow Development Log

Use this file as the durable record of meaningful repository changes.

## Entry Template

### YYYY-MM-DD — <Task title>

**Objective**
- What the task was intended to achieve.

**Prompt / Request**
- Short summary of the Codex task or operator request.

**Relevant skills**
- `.agents/skills/<skill>/SKILL.md`

**Files changed**
- `path/to/file`

**Implementation**
- What changed.
- Important architectural decisions.
- Compatibility considerations.

**Validation / Tests**
- Tests run.
- Windows/Linux/live-device validation where applicable.
- Results.

**Known issues / Limitations**
- Anything intentionally left unresolved.

**Next step**
- Recommended follow-up, if any.

---

## Current Baseline

- OrbitFlow supports a validated Windows Teleport local-port-forward transport.
- OrbitFlow supports a validated Linux/Ubuntu Teleport `ProxyCommand` + SSH certificate + Paramiko `direct-tcpip` transport.
- Both validated paths can establish an interactive Cisco CLI session, dynamically detect the prompt, disable paging, run `show version`, and return cleaned command output.
- Detailed transport rules are maintained in `.agents/skills/jumphost-connectivity/SKILL.md`.

### 2026-09-20 — Linux Teleport bastion host-key loading

**Objective**
- Make strict Linux bastion verification recognize the host keys maintained by Teleport.

**Prompt / Request**
- Load `~/.tsh/known_hosts` in addition to system host keys without changing Windows, target-device verification, or the validated Teleport transport architecture.

**Relevant skills**
- `.agents/skills/jumphost-connectivity/SKILL.md`

**Files changed**
- `src/orbitflow/transport/linux.py`, `tests/test_transport.py`, `README.md`, `DEVLOG.md`

**Implementation**
- Linux live validation found that `tsh` stored the trusted bastion host key in `~/.tsh/known_hosts`, while strict Paramiko verification loaded only normal system host keys.
- Strict Linux bastion setup now loads both sources and preserves `RejectPolicy`; a missing Teleport known-hosts file is treated as optional.
- Windows behavior, target-device host-key behavior, and the `tsh proxy ssh` plus `direct-tcpip` path are unchanged.

**Validation / Tests**
- Added mocked tests for loading Teleport's known-hosts path and tolerating a missing file while remaining in strict mode.

**Known issues / Limitations**
- This change is unit-tested without contacting a live Teleport cluster.

**Next step**
- Re-run Linux live validation with an authenticated operator profile in the deployment environment.

### 2026-09-20 — Configurable SSH host-key verification

**Objective**
- Allow bastion and target host-key verification to be configured independently.

**Prompt / Request**
- Preserve strict verification when enabled, while allowing unknown keys without a `known_hosts` prerequisite when disabled.

**Relevant skills**
- `.agents/skills/jumphost-connectivity/SKILL.md`

**Files changed**
- `src/orbitflow/transport/models.py`, `src/orbitflow/transport/linux.py`, `src/orbitflow/transport/windows.py`
- `tests/test_transport.py`, `README.md`, `DEVLOG.md`

**Implementation**
- Added strict-by-default Linux bastion verification and permissive-by-default target-device verification settings.
- Both Windows and Linux target connections honor the device setting without changing either validated Teleport path.
- Strict mode loads system host keys and rejects unknown keys; permissive mode accepts unknown keys without loading `known_hosts`.

**Validation / Tests**
- Added mocked coverage for enabled and disabled verification on the Linux bastion and on Windows/Linux target devices.

**Known issues / Limitations**
- Permissive verification does not protect against machine-in-the-middle attacks and should only be used when trusted host keys cannot be provisioned.

**Next step**
- Provision trusted target host keys and enable strict device verification where operationally practical.

### 2026-09-20 — Initial Python transport layer

**Objective**
- Provide one common device connection API over the validated Windows and Linux Teleport paths.

**Prompt / Request**
- Implement transport only, with mocked tests, safe cleanup, and no login/OTP automation.

**Relevant skills**
- `.agents/skills/jumphost-connectivity/SKILL.md`

**Files changed**
- `src/orbitflow/transport/*`, `src/orbitflow/__init__.py`, `tests/test_transport.py`
- `requirements.txt`, `README.md`, `.gitignore`, `DEVLOG.md`

**Implementation**
- Added `connect_device`, OS-specific Windows and Linux backends, typed settings, an owned session, and transport exceptions.
- Windows uses a temporary `tsh ssh -N -L` process; Linux uses `tsh proxy ssh`, Teleport key plus certificate, and `direct-tcpip`.
- Rejects unknown SSH host keys and closes resources on success and failure paths.
- Uses the target address, rather than the loopback forward address, for Windows SSH host-key lookup.
- Classifies Linux identity, proxy, and bastion failures as Teleport errors without exposing underlying authentication details.

**Validation / Tests**
- `PYTHONPATH=src pytest -q` passes 6 mock-only tests for both OS paths.
- `ruff check src tests`, `ruff format --check src tests`, `python -m compileall -q src`, and `git diff --check` pass.

**Known issues / Limitations**
- No live-device validation was performed.
- Linux callers must discover and supply key/certificate paths from their active `tsh` profile.
- An authenticated `tsh` session and pre-populated system known-hosts entries are prerequisites.

**Next step**
- Integrate an approved credential provider and active-profile path discovery in a separately scoped task.

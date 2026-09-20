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

"""Huawei VRP stable identity parsing."""

from __future__ import annotations

import re


def parse_huawei_identity(version: str, serial_output: str) -> dict[str, object] | None:
    if not re.search(r"Huawei|VRP.*software", version, re.I):
        return None
    family_match = re.search(r"\bNE05E?\b", version, re.I)
    family = "NE05E" if family_match else "unknown"
    model_match = re.search(r"\bNE05E?[-A-Za-z0-9]*\b", version, re.I)
    serial = _first(
        serial_output,
        r"(?mi)(?:ESN(?:\s+of\s+master)?|Serial Number)\s*:\s*([A-Za-z0-9-]+)",
    )
    software = _first(version, r"(?i)VRP.*?Version\s+([^\s,)]+)")
    uptime = _first(version, r"(?mi)^.+? uptime is (.+)$")
    return dict(hostname="", vendor="Huawei", platform="huawei_vrp",
                device_family=family, hardware_model=model_match.group(0) if model_match else "",
                capability_profile="ne05e" if family == "NE05E" else "unknown",
                capability_flags=("dot1q_subinterface",) if family == "NE05E" else (),
                serial_number=serial, software_version=software, uptime=uptime)


def _first(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

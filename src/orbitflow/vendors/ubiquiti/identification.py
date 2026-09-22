"""Ubiquiti EdgeSwitch stable identity parsing."""

from __future__ import annotations

import re


def parse_edgeswitch_identity(version: str, system: str) -> dict[str, object] | None:
    combined = version + "\n" + system
    if not re.search(r"EdgeSwitch|Ubiquiti", combined, re.I):
        return None
    model = _first(combined, r"(?mi)^(?:Machine Type|Model)\s*[.:]+\s*(.+)$")
    serial = _first(combined, r"(?mi)^Serial Number\s*[.:]+\s*([A-Za-z0-9-]+)")
    software = _first(combined, r"(?mi)^(?:Software Version|Version)\s*[.:]+\s*(\S+)")
    hostname = _first(combined, r"(?mi)^System Name\s*[.:]+\s*(\S+)")
    uptime = _first(combined, r"(?mi)^System Up Time\s*[.:]+\s*(.+)$")
    return dict(hostname=hostname, vendor="Ubiquiti", platform="ubiquiti_edgeswitch",
                device_family="EdgeSwitch", hardware_model=model,
                capability_profile="edgeswitch", capability_flags=("switchport",),
                serial_number=serial, software_version=software, uptime=uptime)


def _first(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

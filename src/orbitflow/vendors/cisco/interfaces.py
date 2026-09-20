"""Cisco interface collection command and parser."""

from __future__ import annotations

import re

from orbitflow.transport import DeviceSession
from orbitflow.vendors.interface_types import InterfaceObservation

from .ios import CiscoIOSCLI

_ROW = re.compile(
    r"^(?P<port>\S+)\s{2,}(?P<status>.+?)\s{2,}(?P<protocol>\S+)"
    r"(?:\s{2,}(?P<description>.*))?$"
)
_REJECTED = re.compile(
    r"%\s*(?:Invalid input|Unknown command|Unrecognized command|Incomplete command)",
    re.IGNORECASE,
)


class CiscoXRCLI(CiscoIOSCLI):
    """IOS-XR shell kept distinct while using its approved Cisco interaction."""


def _state(value: str) -> str:
    normalized = value.strip().lower().replace("-", " ")
    if normalized in {"up", "down"}:
        return normalized
    if normalized in {"admin down", "administratively down"}:
        return "down"
    return normalized


def _is_admin_down(value: str) -> bool:
    return value.strip().lower().replace("-", " ") in {
        "admin down",
        "administratively down",
    }


def parse_interfaces_description(output: str) -> list[InterfaceObservation]:
    """Parse IOS-family ``show interfaces description`` output."""
    if not output.strip():
        return []
    records = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("interface") or set(line) <= {"-", " "}:
            continue
        match = _ROW.match(line)
        if match is None:
            raise ValueError(f"unrecognized Cisco interface row: {line!r}")
        status = match.group("status")
        records.append(
            InterfaceObservation(
                port_name=match.group("port"),
                port_description=(match.group("description") or "").strip(),
                admin_status="down" if _is_admin_down(status) else "up",
                oper_status=_state(match.group("protocol")),
            )
        )
    if not records:
        raise ValueError("Cisco interface output contained no parseable records")
    return records


class CiscoInterfaceAdapter:
    """Collect interfaces for an explicitly selected Cisco platform."""

    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None:
        self._session = session
        self._timeout = timeout

    def collect(self) -> list[InterfaceObservation]:
        cli = self.cli_type(self._session, timeout=self._timeout)
        output = cli.run_command("show interfaces description", timeout=self._timeout)
        if _REJECTED.search(output):
            raise ValueError(
                "Cisco rejected approved command 'show interfaces description'"
            )
        return parse_interfaces_description(output)

    cli_type = CiscoIOSCLI


class CiscoXRInterfaceAdapter(CiscoInterfaceAdapter):
    """IOS-XR-specific adapter, independently selectable by the service."""

    cli_type = CiscoXRCLI

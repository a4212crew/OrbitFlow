"""Ubiquiti EdgeSwitch interface collection command and parser."""

from __future__ import annotations

import re

from orbitflow.transport import DeviceSession
from orbitflow.vendors.common import PromptCLI
from orbitflow.vendors.interface_types import InterfaceCollection, InterfaceObservation

_REJECTED = re.compile(
    r"(?:%\s*(?:Invalid input|Unknown command)|Unrecognized command)", re.IGNORECASE
)
_ROW = re.compile(
    r"^(?P<port>\S+)\s{2,}(?P<name>.*?)\s{2,}(?P<duplex>Full|Half|N/A|Auto)\s+"
    r"(?P<speed>\S+)\s+(?P<neg>\S+)\s+(?P<link>Up|Down|Detached)(?:\s+.*)?$",
    re.IGNORECASE,
)


def extract_edgeswitch_hostname(prompt: str) -> str:
    """Extract the hostname from an EdgeSwitch exec prompt."""
    match = re.fullmatch(r"(?P<hostname>[^:#>\s]+)[#>]", prompt.strip())
    if match is None:
        raise ValueError(f"unrecognized EdgeSwitch prompt: {prompt!r}")
    return match.group("hostname")


def parse_interfaces_status(output: str) -> list[InterfaceObservation]:
    if not output.strip():
        return []
    records = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("port") or set(line) <= {"-", " "}:
            continue
        match = _ROW.match(line)
        if match is None:
            raise ValueError(f"unrecognized EdgeSwitch interface row: {line!r}")
        link = match.group("link").lower()
        records.append(
            InterfaceObservation(
                port_name=match.group("port"),
                port_description=match.group("name").strip(),
                admin_status="",
                oper_status="down" if link == "detached" else link,
            )
        )
    if not records:
        raise ValueError("EdgeSwitch interface output contained no parseable records")
    return records


class EdgeSwitchInterfaceAdapter:
    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None:
        self._session = session
        self._timeout = timeout

    def collect(self) -> InterfaceCollection:
        cli = PromptCLI(
            self._session,
            paging_command="terminal length 0",
            prompt_pattern=r"^([^\r\n]+[>#])[ \t]*$",
            rejected=lambda output: bool(_REJECTED.search(output)),
            platform_name="Ubiquiti EdgeSwitch",
            timeout=self._timeout,
        )
        output = cli.run_command("show interfaces status", timeout=self._timeout)
        if _REJECTED.search(output):
            raise ValueError(
                "EdgeSwitch rejected approved command 'show interfaces status'"
            )
        return InterfaceCollection(
            device_name=extract_edgeswitch_hostname(cli.prompt),
            observations=parse_interfaces_status(output),
        )

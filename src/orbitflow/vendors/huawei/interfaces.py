"""Huawei VRP interface collection command and parser."""

from __future__ import annotations

import re

from orbitflow.transport import DeviceSession
from orbitflow.vendors.common import PromptCLI
from orbitflow.vendors.interface_types import InterfaceObservation

_REJECTED = re.compile(
    r"(?:Error:|Unrecognized command|Wrong parameter|Too many parameters|Incomplete command)",
    re.IGNORECASE,
)
_ROW = re.compile(
    r"^(?P<port>\S+)\s+(?P<phy>\*?(?:up|down))\s+(?P<protocol>up|down)(?:\s+(?P<description>.*))?$",
    re.IGNORECASE,
)


def parse_interface_description(output: str) -> list[InterfaceObservation]:
    if not output.strip():
        return []
    records = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        if (
            not line
            or lower.startswith(("interface", "physical", "*down:"))
            or set(line) <= {"-", " "}
        ):
            continue
        match = _ROW.match(line)
        if match is None:
            raise ValueError(f"unrecognized Huawei interface row: {line!r}")
        phy = match.group("phy").lstrip("*").lower()
        records.append(
            InterfaceObservation(
                port_name=match.group("port"),
                port_description=(match.group("description") or "").strip(),
                admin_status=phy,
                oper_status=match.group("protocol").lower(),
            )
        )
    if not records:
        raise ValueError("Huawei interface output contained no parseable records")
    return records


class HuaweiInterfaceAdapter:
    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None:
        self._session = session
        self._timeout = timeout

    def collect(self) -> list[InterfaceObservation]:
        cli = PromptCLI(
            self._session,
            paging_command="screen-length 0 temporary",
            prompt_pattern=r"^([^\r\n]*(?:<[^<>\r\n]+>|\[[^\[\]\r\n]+\]))[ \t]*$",
            rejected=lambda output: bool(_REJECTED.search(output)),
            platform_name="Huawei VRP",
            timeout=self._timeout,
        )
        output = cli.run_command("display interface description", timeout=self._timeout)
        if _REJECTED.search(output):
            raise ValueError(
                "Huawei VRP rejected approved command 'display interface description'"
            )
        return parse_interface_description(output)

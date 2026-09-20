"""Minimal single-device live validation for the interface capability.

This integration utility intentionally leaves configuration and secret retrieval to
the caller. It is not an inventory or production collection workflow.
"""

from __future__ import annotations

import sys
from typing import TextIO

from orbitflow.capabilities import InterfaceService
from orbitflow.models import InterfaceRecord
from orbitflow.transport import (
    DeviceCredentials,
    DeviceSession,
    TransportConfig,
    connect_device,
)


def run_live_validation(
    device_host: str,
    platform: str,
    credentials: DeviceCredentials,
    transport_config: TransportConfig,
    *,
    device_name: str | None = None,
    output: TextIO = sys.stdout,
) -> list[InterfaceRecord]:
    """Collect and print normalized interfaces for one live device."""
    display_name = device_name or device_host
    session: DeviceSession
    with connect_device(device_host, credentials, transport_config) as session:
        records = InterfaceService().collect(
            session,
            device_name=display_name,
            device_ip=device_host,
            platform=platform,
        )

    print(
        f"{display_name} ({device_host}, {platform}): {len(records)} interface(s)",
        file=output,
    )
    for record in records:
        description = record.port_description or "-"
        admin_status = record.admin_status or "unknown"
        oper_status = record.oper_status or "unknown"
        print(
            f"  {record.port_name}: admin={admin_status}, oper={oper_status}, "
            f"description={description}",
            file=output,
        )
    return records

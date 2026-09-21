"""Minimal single-device live validation for the VLAN capability.

This operator utility is intentionally limited to collecting and displaying the
existing normalized VLAN state. It is not an inventory, policy, reporting, or
provisioning workflow.
"""

from __future__ import annotations

import getpass
import platform as host_platform
import sys
from dataclasses import fields
from pathlib import Path
from typing import TextIO

from orbitflow.capabilities import VlanService
from orbitflow.models import InterfaceVlanObservation, VlanState
from orbitflow.transport import (
    DeviceCredentials,
    DeviceSession,
    TransportConfig,
    connect_device,
)

SUPPORTED_PLATFORMS = (
    "cisco_ios",
    "cisco_xe",
    "cisco_xr",
    "huawei_vrp",
    "ubiquiti_edgeswitch",
)


def _format_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, tuple):
        return ",".join(str(item) for item in value) or "-"
    if value == "":
        return "-"
    return str(value)


def _format_observation(observation: InterfaceVlanObservation) -> str:
    details = ", ".join(
        f"{field.name}={_format_value(getattr(observation, field.name))}"
        for field in fields(observation)
        if field.name not in {"interface_name", "description"}
    )
    return (
        f"  {observation.interface_name}: "
        f"description={_format_value(observation.description)}, {details}"
    )


def run_live_validation(
    device_host: str,
    platform: str,
    credentials: DeviceCredentials,
    transport_config: TransportConfig,
    *,
    device_name: str | None = None,
    output: TextIO = sys.stdout,
) -> VlanState:
    """Collect and print normalized VLAN facts for one live device."""
    session: DeviceSession
    with connect_device(device_host, credentials, transport_config) as session:
        state = VlanService().collect(
            session,
            device_ip=device_host,
            platform=platform,
            device_name=device_name,
        )

    print(f"Device: {state.device_name or device_host}", file=output)
    print(f"Address: {state.device_ip}", file=output)
    print(f"Platform: {state.platform}", file=output)
    print(f"Collected: {state.collection_time.isoformat()}", file=output)
    print(f"\nVLAN/service objects ({len(state.objects)}):", file=output)
    if not state.objects:
        print("  (none observed)", file=output)
    for item in state.objects:
        print(
            f"  type={item.object_type}, id={item.object_id}, "
            f"name={_format_value(item.name)}, vlan_ids={_format_value(item.vlan_ids)}",
            file=output,
        )

    print(f"\nInterface VLAN observations ({len(state.interfaces)}):", file=output)
    if not state.interfaces:
        print("  (none observed)", file=output)
    for observation in state.interfaces:
        print(_format_observation(observation), file=output)
    return state


def _required(prompt: str) -> str:
    while not (value := input(prompt).strip()):
        print("A value is required.", file=sys.stderr)
    return value


def main() -> None:
    """Prompt for one target and invoke the existing transport and capability."""
    device_host = _required("Device IP/host: ")
    platform = _required(f"Platform ({', '.join(SUPPORTED_PLATFORMS)}): ")
    if platform not in SUPPORTED_PLATFORMS:
        raise SystemExit(f"Unsupported platform: {platform}")
    username = _required("Device username: ")
    password = getpass.getpass("Device password: ")
    proxy = _required("Teleport proxy (host:port): ")
    cluster = _required("Teleport cluster: ")
    bastion_host = _required("Bastion host: ")
    bastion_user = _required("Bastion user: ")

    key_path = cert_path = None
    if host_platform.system().lower() == "linux":
        key_path = Path(_required("Teleport private-key path: ")).expanduser()
        cert_path = Path(_required("Teleport SSH-certificate path: ")).expanduser()

    run_live_validation(
        device_host,
        platform,
        DeviceCredentials(username=username, password=password),
        TransportConfig(
            proxy=proxy,
            cluster=cluster,
            bastion_host=bastion_host,
            bastion_user=bastion_user,
            teleport_key_path=key_path,
            teleport_cert_path=cert_path,
        ),
    )


if __name__ == "__main__":
    main()

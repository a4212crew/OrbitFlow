"""Reusable interface description/status capability."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Protocol

from orbitflow.models import InterfaceRecord
from orbitflow.transport import DeviceSession
from orbitflow.vendors.interface_types import InterfaceCollection
from orbitflow.vendors.cisco.interfaces import (
    CiscoInterfaceAdapter,
    CiscoXRInterfaceAdapter,
)
from orbitflow.vendors.huawei.interfaces import HuaweiInterfaceAdapter
from orbitflow.vendors.ubiquiti.interfaces import EdgeSwitchInterfaceAdapter


class InterfaceCapabilityError(Exception):
    """A platform cannot provide a trustworthy interface observation."""


class _InterfaceAdapter(Protocol):
    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None: ...

    def collect(self) -> InterfaceCollection: ...


_ADAPTERS: dict[str, type[_InterfaceAdapter]] = {
    "cisco_ios": CiscoInterfaceAdapter,
    "cisco_xe": CiscoInterfaceAdapter,
    "cisco_xr": CiscoXRInterfaceAdapter,
    "huawei_vrp": HuaweiInterfaceAdapter,
    "ubiquiti_edgeswitch": EdgeSwitchInterfaceAdapter,
}


class InterfaceService:
    """Collect normalized interfaces using an already-established session."""

    def __init__(
        self, clock: Callable[[], datetime] | None = None, *, timeout: float = 10.0
    ) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._timeout = timeout

    def collect(
        self,
        session: DeviceSession,
        *,
        device_ip: str,
        platform: str,
        device_name: str | None = None,
    ) -> list[InterfaceRecord]:
        """Return one common record type without taking ownership of *session*."""
        adapter_type = _ADAPTERS.get(platform)
        if adapter_type is None:
            raise InterfaceCapabilityError(
                f"unsupported interface platform: {platform}"
            )
        try:
            collection = adapter_type(session, timeout=self._timeout).collect()
        except Exception as exc:
            if isinstance(exc, InterfaceCapabilityError):
                raise
            raise InterfaceCapabilityError(
                f"interface collection failed for {device_name or device_ip} "
                f"({device_ip}, {platform}): {exc}"
            ) from exc

        record_device_name = device_name or collection.device_name
        collected_at = self._clock()
        return [
            InterfaceRecord(
                device_name=record_device_name,
                device_ip=device_ip,
                platform=platform,
                port_name=item.port_name,
                port_description=item.port_description,
                admin_status=item.admin_status,
                oper_status=item.oper_status,
                collection_time=collected_at,
            )
            for item in collection.observations
        ]

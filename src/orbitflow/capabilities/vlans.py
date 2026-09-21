"""Reusable read-only VLAN observation capability."""

from datetime import datetime, timezone
from typing import Callable, Protocol

from orbitflow.models import VlanState
from orbitflow.transport import DeviceSession
from orbitflow.vendors.vlan_types import VlanCollection
from orbitflow.vendors.cisco.vlans import (
    CiscoVlanAdapter,
    CiscoXEVlanAdapter,
    CiscoXRVlanAdapter,
)
from orbitflow.vendors.huawei.vlans import HuaweiVlanAdapter
from orbitflow.vendors.ubiquiti.vlans import EdgeSwitchVlanAdapter


class VlanCapabilityError(Exception):
    """A platform cannot provide a trustworthy VLAN observation."""


class _Adapter(Protocol):
    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None: ...
    def collect(self) -> VlanCollection: ...


_ADAPTERS: dict[str, type[_Adapter]] = {
    "cisco_ios": CiscoVlanAdapter,
    "cisco_xe": CiscoXEVlanAdapter,
    "cisco_xr": CiscoXRVlanAdapter,
    "huawei_vrp": HuaweiVlanAdapter,
    "ubiquiti_edgeswitch": EdgeSwitchVlanAdapter,
}


class VlanService:
    """Collect configured VLAN facts through an established device session."""

    def __init__(
        self, clock: Callable[[], datetime] | None = None, *, timeout: float = 10.0
    ) -> None:
        self._clock, self._timeout = (
            clock or (lambda: datetime.now(timezone.utc)),
            timeout,
        )

    def collect(
        self,
        session: DeviceSession,
        *,
        device_ip: str,
        platform: str,
        device_name: str | None = None,
    ) -> VlanState:
        adapter = _ADAPTERS.get(platform)
        if adapter is None:
            raise VlanCapabilityError(f"unsupported VLAN platform: {platform}")
        try:
            result = adapter(session, timeout=self._timeout).collect()
        except Exception as exc:
            raise VlanCapabilityError(
                f"VLAN collection failed for {device_name or device_ip} ({device_ip}, {platform}): {exc}"
            ) from exc
        return VlanState(
            device_name or result.device_name,
            device_ip,
            platform,
            result.interfaces,
            result.objects,
            self._clock(),
        )

"""Normalized models shared by device capabilities and their consumers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class InterfaceRecord:
    """Vendor-neutral interface description and state observation."""

    device_name: str
    device_ip: str
    platform: str
    port_name: str
    port_description: str
    admin_status: str
    oper_status: str
    collection_time: datetime


@dataclass(frozen=True)
class VlanObject:
    """A configured VLAN or vendor service object (identities are not conflated)."""

    object_type: str
    object_id: str
    name: str = ""
    vlan_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class InterfaceVlanObservation:
    """Configured VLAN facts for one interface or one service on it."""

    interface_name: str
    description: str = ""
    mode: str = "unknown"
    access_vlan: Optional[int] = None
    native_vlan: Optional[int] = None
    pvid: Optional[int] = None
    allowed_vlans: Optional[tuple[int, ...]] = None
    tagged_vlans: tuple[int, ...] = ()
    untagged_vlans: tuple[int, ...] = ()
    excluded_vlans: tuple[int, ...] = ()
    service_vlan: Optional[int] = None
    control_vlan: Optional[int] = None
    outer_vlan: Optional[int] = None
    inner_vlan: Optional[int] = None
    referenced_vlans: tuple[int, ...] = ()
    vlan_source: str = ""
    vlan_database_applicable: bool = True
    service_binding_type: str = ""
    service_binding_name: str = ""


@dataclass(frozen=True)
class VlanState:
    """Vendor-neutral snapshot returned by :class:`VlanService`."""

    device_name: str
    device_ip: str
    platform: str
    interfaces: tuple[InterfaceVlanObservation, ...]
    objects: tuple[VlanObject, ...]
    collection_time: datetime


@dataclass(frozen=True)
class DeviceContext:
    """Latest observed stable identity and capability-selection context."""

    device_id: str
    management_ip: str
    observed_management_ips: tuple[str, ...]
    hostname: str
    vendor: str
    platform: str
    device_family: str
    hardware_model: str
    capability_profile: str
    capability_flags: tuple[str, ...]
    serial_number: str
    software_version: str
    uptime: str
    last_successful_collection: datetime
    last_collection_attempt: datetime
    collection_status: str = "success"
    collection_error: str = ""

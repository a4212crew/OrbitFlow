"""Normalized models shared by device capabilities and their consumers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


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

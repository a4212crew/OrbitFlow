"""Internal vendor-parser observation type."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InterfaceObservation:
    port_name: str
    port_description: str = ""
    admin_status: str = ""
    oper_status: str = ""

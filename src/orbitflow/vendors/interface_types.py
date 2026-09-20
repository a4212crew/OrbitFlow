"""Internal vendor-parser observation type."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InterfaceObservation:
    port_name: str
    port_description: str = ""
    admin_status: str = ""
    oper_status: str = ""


@dataclass(frozen=True)
class InterfaceCollection:
    """Vendor collection result with identity learned from the device prompt."""

    device_name: str
    observations: list[InterfaceObservation]

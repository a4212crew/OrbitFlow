"""Internal result type and VLAN-list parsing shared by vendor adapters."""

from dataclasses import dataclass
import re

from orbitflow.models import InterfaceVlanObservation, VlanObject


@dataclass(frozen=True)
class VlanCollection:
    device_name: str
    interfaces: tuple[InterfaceVlanObservation, ...]
    objects: tuple[VlanObject, ...]


def parse_vlan_list(value: str, *, range_word: str = "-") -> tuple[int, ...]:
    """Expand comma/space separated VLAN IDs and inclusive ranges deterministically."""
    text = value.strip()
    if not text:
        return ()
    if range_word == "to":
        text = re.sub(r"\s+to\s+", "-", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*-\s*", "-", text.replace(",", " "))
    result: set[int] = set()
    for token in text.split():
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", token)
        if not match:
            raise ValueError(f"invalid VLAN list token: {token!r}")
        first = int(match.group(1))
        last = int(match.group(2) or first)
        if not 1 <= first <= 4094 or not 1 <= last <= 4094 or last < first:
            raise ValueError(f"invalid VLAN range: {token!r}")
        result.update(range(first, last + 1))
    return tuple(sorted(result))

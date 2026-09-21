"""Cisco IOS, IOS-XE, and IOS-XR running-configuration VLAN observation."""

from __future__ import annotations

import re

from orbitflow.models import InterfaceVlanObservation, VlanObject
from orbitflow.transport import DeviceSession
from orbitflow.vendors.vlan_types import VlanCollection, parse_vlan_list

from .interfaces import CiscoXRCLI, extract_ios_xr_hostname
from .ios import CiscoIOSCLI, extract_ios_hostname

_REJECTED = re.compile(
    r"%\s*(?:Invalid input|Unknown command|Unrecognized command|Incomplete command)",
    re.I,
)


def _blocks(output: str) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    heading = ""
    body: list[str] = []
    for raw in output.splitlines() + ["!"]:
        line = raw.rstrip()
        if line and not line[0].isspace() and line != "!":
            if heading:
                blocks.append((heading, body))
            heading, body = line.strip(), []
        elif line == "!":
            if heading:
                blocks.append((heading, body))
            heading, body = "", []
        elif heading:
            body.append(line.strip())
    return blocks


def _description(lines: list[str]) -> str:
    return next((line[12:] for line in lines if line.startswith("description ")), "")


def parse_ios_running_config(
    output: str, *, evc: bool = False
) -> tuple[tuple[InterfaceVlanObservation, ...], tuple[VlanObject, ...]]:
    interfaces: list[InterfaceVlanObservation] = []
    objects: list[VlanObject] = []
    for heading, lines in _blocks(output):
        vlan = re.fullmatch(r"vlan (.+)", heading)
        if vlan:
            vlan_ids = parse_vlan_list(vlan.group(1))
            name = next((x[5:] for x in lines if x.startswith("name ")), "")
            objects.extend(
                VlanObject(
                    "vlan",
                    str(vid),
                    name if len(vlan_ids) == 1 else "",
                    (vid,),
                )
                for vid in vlan_ids
            )
            continue
        match = re.fullmatch(r"interface (.+)", heading)
        if not match:
            continue
        name, description = match.group(1), _description(lines)
        mode_line = next((x for x in lines if x.startswith("switchport mode ")), "")
        access = next((x for x in lines if x.startswith("switchport access vlan ")), "")
        native = next(
            (x for x in lines if x.startswith("switchport trunk native vlan ")), ""
        )
        allowed = next(
            (x for x in lines if x.startswith("switchport trunk allowed vlan ")), ""
        )
        if mode_line or access or native or allowed:
            mode = mode_line.rsplit(" ", 1)[-1] if mode_line else "unknown"
            access_id = int(access.rsplit(" ", 1)[-1]) if access else None
            native_id = int(native.rsplit(" ", 1)[-1]) if native else None
            allowed_ids = (
                parse_vlan_list(allowed.split("vlan ", 1)[1]) if allowed else None
            )
            refs = (
                set(allowed_ids or ())
                | ({access_id} if access_id else set())
                | ({native_id} if native_id else set())
            )
            interfaces.append(
                InterfaceVlanObservation(
                    name,
                    description,
                    mode,
                    access_vlan=access_id,
                    native_vlan=native_id,
                    allowed_vlans=allowed_ids,
                    untagged_vlans=(access_id,) if access_id else (),
                    referenced_vlans=tuple(sorted(refs)),
                    vlan_source="switchport",
                )
            )
        if evc:
            current: list[str] | None = None
            sid = ""
            for line in lines + ["service instance end ethernet"]:
                sm = re.fullmatch(r"service instance (\S+) ethernet", line)
                if sm:
                    if current is not None:
                        interfaces.append(_evc(name, description, sid, current))
                    sid, current = sm.group(1), []
                elif current is not None:
                    current.append(line)
    return tuple(interfaces), tuple(objects)


def _evc(
    name: str, description: str, sid: str, lines: list[str]
) -> InterfaceVlanObservation:
    encap = next((x for x in lines if x.startswith("encapsulation dot1q ")), "")
    bridge = next((x for x in lines if x.startswith("bridge-domain ")), "")
    vlan = int(encap.split()[2]) if encap and encap.split()[2].isdigit() else None
    return InterfaceVlanObservation(
        name,
        description,
        "service",
        service_vlan=vlan,
        outer_vlan=vlan,
        referenced_vlans=(vlan,) if vlan else (),
        vlan_source="service-instance",
        vlan_database_applicable=False,
        service_binding_type="bridge-domain" if bridge else "service-instance",
        service_binding_name=bridge.split(maxsplit=1)[1] if bridge else sid,
    )


def parse_ios_xr_running_config(
    output: str,
) -> tuple[tuple[InterfaceVlanObservation, ...], tuple[VlanObject, ...]]:
    interfaces: list[InterfaceVlanObservation] = []
    objects: list[VlanObject] = []
    bindings: dict[str, tuple[str, str]] = {}
    current_bg = current_bd = ""
    for heading, lines in _blocks(output):
        if heading.startswith("l2vpn"):
            # l2vpn is commonly one indentation hierarchy; retain its semantic nesting.
            stack: list[tuple[int, str]] = []
            for raw in lines:
                indent = len(raw) - len(raw.lstrip())
                line = raw.strip()
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                if line.startswith("bridge group "):
                    current_bg = line[13:]
                elif line.startswith("bridge-domain "):
                    current_bd = line[14:]
                    objects.append(
                        VlanObject(
                            "bridge-domain", f"{current_bg}/{current_bd}", current_bd
                        )
                    )
                elif line.startswith("interface "):
                    bindings[line[10:].split()[0]] = (
                        "bridge-domain",
                        f"{current_bg}/{current_bd}",
                    )
                elif line.startswith("routed interface "):
                    bindings[line[17:]] = (
                        "bridge-domain",
                        f"{current_bg}/{current_bd}",
                    )
                stack.append((indent, line))
            continue
        match = re.fullmatch(r"interface (.+?)(?: (l2transport))?", heading)
        if not match:
            continue
        name, l2 = match.group(1), bool(match.group(2))
        encap = next(
            (
                x
                for x in lines
                if x.startswith("encapsulation dot1q ") or x == "encapsulation untagged"
            ),
            "",
        )
        if not encap and name not in bindings:
            continue
        vlan = inner_vlan = None
        if encap.startswith("encapsulation dot1q "):
            tokens = encap.split()
            token = tokens[2]
            vlan = int(token) if token.isdigit() else None
            if "second-dot1q" in tokens:
                inner_token = tokens[tokens.index("second-dot1q") + 1]
                inner_vlan = int(inner_token) if inner_token.isdigit() else None
        binding = bindings.get(name, ("", ""))
        interfaces.append(
            InterfaceVlanObservation(
                name,
                _description(lines),
                "service" if l2 else "routed_subinterface",
                service_vlan=vlan,
                outer_vlan=vlan,
                inner_vlan=inner_vlan,
                untagged_vlans=() if vlan else (() if not encap else ()),
                referenced_vlans=tuple(
                    item for item in (vlan, inner_vlan) if item is not None
                ),
                vlan_source="dot1q" if vlan else "untagged",
                vlan_database_applicable=False,
                service_binding_type=binding[0],
                service_binding_name=binding[1],
            )
        )
    # Bindings are parsed after interface blocks in normal configs; patch immutably.
    interfaces = [
        (
            obs
            if obs.interface_name not in bindings
            else InterfaceVlanObservation(
                **{
                    **obs.__dict__,
                    "service_binding_type": bindings[obs.interface_name][0],
                    "service_binding_name": bindings[obs.interface_name][1],
                }
            )
        )
        for obs in interfaces
    ]
    return tuple(interfaces), tuple(objects)


class CiscoVlanAdapter:
    def __init__(
        self, session: DeviceSession, *, timeout: float = 10.0, evc: bool = False
    ) -> None:
        self._session, self._timeout, self._evc = session, timeout, evc

    def collect(self) -> VlanCollection:
        cli = CiscoIOSCLI(self._session, timeout=self._timeout)
        output = cli.run_command("show running-config", timeout=self._timeout)
        if _REJECTED.search(output):
            raise ValueError("Cisco rejected approved command 'show running-config'")
        interfaces, objects = parse_ios_running_config(output, evc=self._evc)
        return VlanCollection(extract_ios_hostname(cli.prompt), interfaces, objects)


class CiscoXEVlanAdapter(CiscoVlanAdapter):
    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None:
        super().__init__(session, timeout=timeout, evc=True)


class CiscoXRVlanAdapter:
    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None:
        self._session, self._timeout = session, timeout

    def collect(self) -> VlanCollection:
        cli = CiscoXRCLI(self._session, timeout=self._timeout)
        output = cli.run_command("show running-config", timeout=self._timeout)
        if _REJECTED.search(output):
            raise ValueError(
                "Cisco IOS-XR rejected approved command 'show running-config'"
            )
        interfaces, objects = parse_ios_xr_running_config(output)
        return VlanCollection(extract_ios_xr_hostname(cli.prompt), interfaces, objects)

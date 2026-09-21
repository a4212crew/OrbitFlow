"""Huawei VRP current-configuration VLAN observation."""

import re

from orbitflow.models import InterfaceVlanObservation, VlanObject
from orbitflow.transport import DeviceSession
from orbitflow.vendors.common import PromptCLI
from orbitflow.vendors.vlan_types import VlanCollection, parse_vlan_list
from .interfaces import extract_huawei_hostname

_REJECTED = re.compile(
    r"(?:Error:.*(?:Unrecognized|Wrong parameter)|\^\s*$)", re.I | re.M
)


def parse_huawei_config(
    output: str,
) -> tuple[tuple[InterfaceVlanObservation, ...], tuple[VlanObject, ...]]:
    database: set[int] = set()
    interfaces: list[InterfaceVlanObservation] = []
    sections = re.split(r"^#\s*$", output, flags=re.M)
    for section in sections:
        lines = [x.strip() for x in section.splitlines() if x.strip()]
        if not lines:
            continue
        for line in lines:
            if line.startswith("vlan batch "):
                database.update(parse_vlan_list(line[11:], range_word="to"))
        match = re.fullmatch(r"interface (.+)", lines[0])
        if not match:
            continue
        name = match.group(1)
        description = next((x[12:] for x in lines if x.startswith("description ")), "")
        access = next((x for x in lines if x.startswith("port default vlan ")), "")
        trunk = next(
            (x for x in lines if x.startswith("port trunk allow-pass vlan ")), ""
        )
        dot1q = next((x for x in lines if x.startswith("vlan-type dot1q ")), "")
        termination = next(
            (x for x in lines if x.startswith("dot1q termination vid ")), ""
        )
        control = next(
            (x for x in lines if re.fullmatch(r"control-vid \d+ dot1q-termination", x)),
            "",
        )
        vsi = next((x for x in lines if x.startswith("l2 binding vsi ")), "")
        if name.lower().startswith("vlanif") and name[6:].isdigit():
            vlan = int(name[6:])
            interfaces.append(
                InterfaceVlanObservation(
                    name,
                    description,
                    "svi",
                    access_vlan=vlan,
                    referenced_vlans=(vlan,),
                    vlan_source="Vlanif",
                )
            )
        elif access:
            vlan = int(access.rsplit(" ", 1)[-1])
            interfaces.append(
                InterfaceVlanObservation(
                    name,
                    description,
                    "access",
                    access_vlan=vlan,
                    untagged_vlans=(vlan,),
                    referenced_vlans=(vlan,),
                    vlan_source="port-default-vlan",
                )
            )
        elif trunk:
            vlans = parse_vlan_list(trunk[27:], range_word="to")
            interfaces.append(
                InterfaceVlanObservation(
                    name,
                    description,
                    "trunk",
                    allowed_vlans=vlans,
                    tagged_vlans=vlans,
                    referenced_vlans=vlans,
                    vlan_source="allow-pass",
                )
            )
        elif dot1q or termination or control or vsi:
            source = dot1q or termination or control
            vlan_match = re.search(
                r"(?:vlan-type dot1q|termination vid|control-vid)\s+(\d+)", source
            )
            service_vlan = int(vlan_match.group(1)) if vlan_match else None
            interfaces.append(
                InterfaceVlanObservation(
                    name,
                    description,
                    (
                        "service"
                        if (termination or control or vsi)
                        else "routed_subinterface"
                    ),
                    service_vlan=service_vlan,
                    outer_vlan=service_vlan,
                    referenced_vlans=(service_vlan,) if service_vlan else (),
                    vlan_source=(
                        "dot1q-termination"
                        if (termination or control)
                        else "vlan-type-dot1q"
                    ),
                    vlan_database_applicable=False,
                    service_binding_type="vsi" if vsi else "",
                    service_binding_name=vsi[15:] if vsi else "",
                )
            )
    objects = tuple(
        VlanObject("vlan", str(vlan), vlan_ids=(vlan,)) for vlan in sorted(database)
    )
    return tuple(interfaces), objects


class HuaweiVlanAdapter:
    def __init__(self, session: DeviceSession, *, timeout: float = 10.0) -> None:
        self._session, self._timeout = session, timeout

    def collect(self) -> VlanCollection:
        cli = PromptCLI(
            self._session,
            paging_command="screen-length 0 temporary",
            prompt_pattern=r"^([^\r\n]*(?:<[^<>\r\n]+>|\[[^\[\]\r\n]+\]))[ \t]*$",
            rejected=lambda x: bool(_REJECTED.search(x)),
            platform_name="Huawei VRP",
            timeout=self._timeout,
        )
        output = cli.run_command("display current-configuration", timeout=self._timeout)
        if _REJECTED.search(output):
            raise ValueError(
                "Huawei VRP rejected approved command 'display current-configuration'"
            )
        interfaces, objects = parse_huawei_config(output)
        return VlanCollection(extract_huawei_hostname(cli.prompt), interfaces, objects)

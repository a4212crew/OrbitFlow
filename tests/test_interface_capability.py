from datetime import datetime, timezone

import pytest

from orbitflow.capabilities import InterfaceCapabilityError, InterfaceService
from orbitflow.transport import DeviceSession
from orbitflow.vendors.cisco.interfaces import (
    extract_ios_xr_hostname,
    parse_ios_xr_interfaces_description,
    parse_interfaces_description,
)
from orbitflow.vendors.cisco.ios import extract_ios_hostname
from orbitflow.vendors.huawei.interfaces import (
    extract_huawei_hostname,
    parse_interface_description,
)
from orbitflow.vendors.ubiquiti.interfaces import extract_edgeswitch_hostname


class FakeChannel:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.sent = []

    def sendall(self, data):
        self.sent.append(data)

    def settimeout(self, _timeout):
        pass

    def recv(self, _size):
        return next(self.responses)


def make_session(responses):
    channel = FakeChannel(responses)

    class Client:
        def invoke_shell(self, **_kwargs):
            return channel

    return DeviceSession(Client(), lambda: None), channel


CASES = {
    "cisco_ios": {
        "prompt": "ios#",
        "paging": "terminal length 0",
        "command": "show interfaces description",
        "output": (
            "Interface                      Status         Protocol Description\r\n"
            "Gi0/0/0                       up             up       Customer uplink west\r\n"
            "Gi0/0/1                       admin down     down     Spare port"
        ),
        "rejection": "% Invalid input detected at '^' marker.",
    },
    "cisco_xe": {
        "prompt": "xe#",
        "paging": "terminal length 0",
        "command": "show interfaces description",
        "output": (
            "Interface                      Status         Protocol Description\r\n"
            "Te0/0/0                       up             down     Metro handoff east"
        ),
        "rejection": "% Invalid input detected at '^' marker.",
    },
    "cisco_xr": {
        "prompt": "RP/0/RSP0/CPU0:xr#",
        "paging": "terminal length 0",
        "command": "show interfaces description",
        "output": (
            "Interface          Status      Protocol    Description\r\n"
            "Gi0/0/0/0          up          up          Core link north"
        ),
        "rejection": "% Invalid input detected at '^' marker.",
    },
    "huawei_vrp": {
        "prompt": "<NE05E>",
        "paging": "screen-length 0 temporary",
        "command": "display interface description",
        "output": (
            "Interface                         PHY   Protocol Description\r\n"
            "GE0/0/0                           up    up       Customer access one\r\n"
            "GE0/0/1                           *down down     Disabled spare port"
        ),
        "rejection": "Error: Unrecognized command found at '^' position.",
    },
    "ubiquiti_edgeswitch": {
        "prompt": "edgeswitch#",
        "paging": "terminal length 0",
        "command": "show interfaces status",
        "output": (
            "Port      Name                       Duplex Speed  Neg Link Flow M VLAN\r\n"
            "0/1       Customer office west       Full   1000   Auto Up   Off  A 10\r\n"
            "0/2       Spare port                  Auto   N/A    Auto Down Off  A 1"
        ),
        "rejection": "% Invalid input detected at '^' marker.",
    },
}


def run_collection(platform, output=None, setup_output="", device_name="edge-01"):
    case = CASES[platform]
    prompt = case["prompt"]
    paging = case["paging"]
    command = case["command"]
    session, channel = make_session(
        [
            prompt.encode(),
            f"{paging}\r\n{setup_output}\r\n{prompt}".encode(),
            f"{command}\r\n{case['output'] if output is None else output}\r\n{prompt}".encode(),
        ]
    )
    now = datetime(2026, 9, 20, 12, tzinfo=timezone.utc)
    records = InterfaceService(lambda: now).collect(
        session,
        device_ip="192.0.2.10",
        platform=platform,
        device_name=device_name,
    )
    return records, channel, now


@pytest.mark.parametrize("platform", CASES)
def test_every_platform_disables_paging_and_uses_only_approved_command(platform):
    _records, channel, _now = run_collection(platform)
    case = CASES[platform]

    assert channel.sent == [
        b"\n",
        f"{case['paging']}\n".encode(),
        f"{case['command']}\n".encode(),
    ]


@pytest.mark.parametrize("platform", CASES)
def test_every_platform_normalizes_status_and_descriptions_with_spaces(platform):
    records, _channel, now = run_collection(platform)

    first = records[0]
    assert first.device_name == "edge-01"
    assert first.device_ip == "192.0.2.10"
    assert first.platform == platform
    assert " " in first.port_description
    assert first.oper_status in {"up", "down"}
    assert first.collection_time == now
    if platform == "ubiquiti_edgeswitch":
        assert first.admin_status == ""
    else:
        assert first.admin_status == "up"


@pytest.mark.parametrize("platform", CASES)
def test_every_platform_uses_prompt_hostname_when_name_is_omitted(platform):
    records, _channel, _now = run_collection(platform, device_name=None)

    expected = "xr" if platform == "cisco_xr" else CASES[platform]["prompt"][:-1]
    if platform == "huawei_vrp":
        expected = "NE05E"
    assert records[0].device_name == expected


@pytest.mark.parametrize("prompt", ["branch-router#", "branch-router>"])
def test_ios_and_ios_xe_hostname_extraction(prompt):
    assert extract_ios_hostname(prompt) == "branch-router"


def test_ios_xr_hostname_extraction():
    assert extract_ios_xr_hostname("RP/0/RSP0/CPU0:core-xr-01#") == "core-xr-01"


def test_ios_xr_parser_ignores_device_timestamp_before_interface_table():
    records = parse_ios_xr_interfaces_description(
        "Sun Sep 20 20:15:28.579 AEST\n"
        "Interface          Status      Protocol    Description\n"
        "Gi0/0/0/0          up          up          Core link north"
    )

    assert records[0].port_name == "Gi0/0/0/0"
    assert records[0].port_description == "Core link north"


def test_ios_parser_remains_strict_about_ios_xr_timestamp():
    with pytest.raises(ValueError, match="unrecognized Cisco interface row"):
        parse_interfaces_description(
            "Sun Sep 20 20:15:28.579 AEST\n"
            "Interface          Status      Protocol    Description\n"
            "Gi0/0/0/0          up          up          Core link north"
        )


def test_ios_xr_parser_remains_strict_after_interface_table_starts():
    with pytest.raises(ValueError, match="unrecognized Cisco interface row"):
        parse_ios_xr_interfaces_description(
            "Interface          Status      Protocol    Description\n"
            "Sun Sep 20 20:15:28.579 AEST"
        )


@pytest.mark.parametrize("prompt", ["<NE05E-01>", "[NE05E-01]"])
def test_huawei_hostname_extraction(prompt):
    assert extract_huawei_hostname(prompt) == "NE05E-01"


@pytest.mark.parametrize("prompt", ["edge-switch-01#", "edge-switch-01>"])
def test_edgeswitch_hostname_extraction(prompt):
    assert extract_edgeswitch_hostname(prompt) == "edge-switch-01"


@pytest.mark.parametrize("platform", CASES)
def test_every_platform_returns_no_records_for_empty_command_output(platform):
    records, _channel, _now = run_collection(platform, output="")
    assert records == []


@pytest.mark.parametrize("platform", CASES)
def test_every_platform_reports_parser_failure(platform):
    with pytest.raises(InterfaceCapabilityError, match="interface collection failed"):
        run_collection(platform, output="this is not a valid interface table")


@pytest.mark.parametrize("platform", CASES)
def test_every_platform_reports_rejected_session_setup(platform):
    case = CASES[platform]
    prompt = case["prompt"]
    paging = case["paging"]
    session, channel = make_session(
        [
            prompt.encode(),
            f"{paging}\r\n{case['rejection']}\r\n{prompt}".encode(),
        ]
    )

    with pytest.raises(
        InterfaceCapabilityError, match="rejected required session setup command"
    ):
        InterfaceService().collect(
            session,
            device_name="edge-01",
            device_ip="192.0.2.10",
            platform=platform,
        )
    assert channel.sent == [b"\n", f"{paging}\n".encode()]


@pytest.mark.parametrize("platform", CASES)
def test_every_platform_reports_rejected_collection_command_without_guessing(platform):
    case = CASES[platform]
    with pytest.raises(InterfaceCapabilityError, match="rejected approved command"):
        run_collection(platform, output=case["rejection"])


def test_unsupported_platform_is_a_clear_capability_error():
    session, _channel = make_session([])
    with pytest.raises(
        InterfaceCapabilityError, match="unsupported interface platform"
    ):
        InterfaceService().collect(
            session,
            device_name="device",
            device_ip="192.0.2.20",
            platform="generic",
        )


def test_huawei_phy_normalization_distinguishes_physical_and_admin_down():
    records = parse_interface_description(
        "Interface  PHY  Protocol  Description\n"
        "GE0/0/0    up   down      Protocol differs\n"
        "GE0/0/1    down up        Physical down\n"
        "GE0/0/2    *down up       Administratively down"
    )

    assert [(item.admin_status, item.oper_status) for item in records] == [
        ("up", "up"),
        ("up", "down"),
        ("down", "down"),
    ]


@pytest.mark.parametrize(
    "status", ["admin-down", "admin down", "administratively down"]
)
def test_cisco_xr_admin_down_spellings_normalize_to_down(status):
    records = parse_interfaces_description(
        "Interface  Status  Protocol  Description\n"
        f"Gi0/0/0/0  {status}  down      Maintenance"
    )

    assert records[0].admin_status == "down"
    assert records[0].oper_status == "down"

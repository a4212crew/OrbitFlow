from unittest.mock import MagicMock

import paramiko
import pytest

from orbitflow.transport import DeviceCredentials
from orbitflow.transport.authentication import connect_target


@pytest.fixture
def credentials():
    return DeviceCredentials(username="device-user", password="secret")


def test_normal_password_authentication_succeeds_without_interactive_retry(credentials):
    client = MagicMock()

    connect_target(client, "192.0.2.10", credentials, port=22)

    client.connect.assert_called_once_with(
        "192.0.2.10",
        username="device-user",
        password="secret",
        pkey=None,
        port=22,
    )
    client.get_transport.assert_not_called()


def test_password_failure_retries_with_keyboard_interactive(credentials):
    client = MagicMock()
    client.connect.side_effect = paramiko.AuthenticationException("rejected")
    transport = client.get_transport.return_value
    transport.is_active.return_value = True

    connect_target(client, "192.0.2.10", credentials)

    handler = transport.auth_interactive.call_args.args[1]
    assert handler("login", "", [("Password: ", False)]) == ["secret"]
    transport.auth_interactive.assert_called_once_with("device-user", handler)


def test_keyboard_interactive_rejects_non_password_prompt(credentials):
    client = MagicMock()
    client.connect.side_effect = paramiko.AuthenticationException("rejected")
    transport = client.get_transport.return_value
    transport.is_active.return_value = True

    def request_unrelated_prompt(_username, handler):
        handler("verification", "", [("OTP: ", False)])

    transport.auth_interactive.side_effect = request_unrelated_prompt

    with pytest.raises(paramiko.AuthenticationException, match="non-password"):
        connect_target(client, "192.0.2.10", credentials)


def test_keyboard_interactive_authentication_failure_is_propagated(credentials):
    client = MagicMock()
    client.connect.side_effect = paramiko.AuthenticationException("rejected")
    transport = client.get_transport.return_value
    transport.is_active.return_value = True
    transport.auth_interactive.side_effect = paramiko.AuthenticationException(
        "interactive rejected"
    )

    with pytest.raises(paramiko.AuthenticationException, match="interactive rejected"):
        connect_target(client, "192.0.2.10", credentials)


def test_keyboard_interactive_is_not_tried_when_server_does_not_offer_it(credentials):
    client = MagicMock()
    client.connect.side_effect = paramiko.BadAuthenticationType(
        "rejected", ["publickey"]
    )

    with pytest.raises(paramiko.BadAuthenticationType):
        connect_target(client, "192.0.2.10", credentials)

    client.get_transport.assert_not_called()

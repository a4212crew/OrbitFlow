from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orbitflow.transport import (
    DeviceCredentials,
    TransportConfig,
    TransportConfigurationError,
    UnsupportedPlatformError,
    connect_device,
)
from orbitflow.transport.linux import connect_linux
from orbitflow.transport.windows import connect_windows


@pytest.fixture
def credentials():
    return DeviceCredentials(username="device-user", password="not-a-real-password")


@pytest.fixture
def config():
    return TransportConfig(
        proxy="teleport.example.test:443",
        cluster="example-cluster",
        bastion_host="example-bastion",
        bastion_user="teleport-user",
        teleport_key_path=Path("/profile/key"),
        teleport_cert_path=Path("/profile/key-cert.pub"),
        tsh_path="/usr/bin/tsh",
    )


def test_connect_device_dispatches_without_exposing_os_details(credentials, config):
    expected = MagicMock()
    with patch(
        "orbitflow.transport.windows.connect_windows", return_value=expected
    ) as connect:
        result = connect_device("192.0.2.10", credentials, config, system="Windows")
    assert result is expected
    connect.assert_called_once_with("192.0.2.10", credentials, config)


def test_connect_device_rejects_unsupported_os(credentials, config):
    with pytest.raises(UnsupportedPlatformError):
        connect_device("192.0.2.10", credentials, config, system="Darwin")


@patch("orbitflow.transport.windows._wait_for_tunnel")
@patch("orbitflow.transport.windows.socket.create_connection")
@patch("orbitflow.transport.windows._free_local_port", return_value=49152)
@patch("orbitflow.transport.windows.subprocess.Popen")
@patch("orbitflow.transport.windows.paramiko.SSHClient")
def test_windows_uses_tsh_forward_and_cleans_up(
    ssh_client,
    popen,
    _free_port,
    create_connection,
    wait_for_tunnel,
    credentials,
    config,
):
    process = popen.return_value
    process.poll.return_value = None
    client = ssh_client.return_value
    forwarded_socket = create_connection.return_value

    session = connect_windows("192.0.2.10", credentials, config)

    command = popen.call_args.args[0]
    assert command[:5] == [
        "/usr/bin/tsh",
        "ssh",
        "--cluster",
        "example-cluster",
        "--proxy",
    ]
    assert "127.0.0.1:49152:192.0.2.10:22" in command
    wait_for_tunnel.assert_called_once_with(process, 49152, 15.0)
    client.connect.assert_called_once_with(
        "192.0.2.10",
        port=22,
        username="device-user",
        password="not-a-real-password",
        pkey=None,
        sock=forwarded_socket,
        timeout=15.0,
    )

    session.close()
    session.close()
    client.close.assert_called_once_with()
    forwarded_socket.close.assert_called_once_with()
    process.terminate.assert_called_once_with()


@patch("orbitflow.transport.linux.paramiko.ProxyCommand")
@patch("orbitflow.transport.linux.paramiko.PKey.from_path")
@patch("orbitflow.transport.linux.paramiko.SSHClient")
def test_linux_uses_certificate_and_direct_tcpip(
    ssh_client, from_path, proxy_command, credentials, config
):
    bastion, target = MagicMock(), MagicMock()
    ssh_client.side_effect = [bastion, target]
    transport = bastion.get_transport.return_value
    transport.is_active.return_value = True
    channel = transport.open_channel.return_value
    key = from_path.return_value
    proxy = proxy_command.return_value

    session = connect_linux("192.0.2.10", credentials, config)

    from_path.assert_called_once_with("/profile/key")
    key.load_certificate.assert_called_once_with("/profile/key-cert.pub")
    assert "tsh proxy ssh" in proxy_command.call_args.args[0]
    transport.open_channel.assert_called_once_with(
        "direct-tcpip", ("192.0.2.10", 22), ("127.0.0.1", 0)
    )
    assert target.connect.call_args.kwargs["sock"] is channel

    session.close()
    assert target.close.call_count == 1
    assert channel.close.call_count == 1
    assert bastion.close.call_count == 1
    assert proxy.close.call_count == 1


def test_linux_requires_explicit_active_profile_paths(credentials, config):
    incomplete = TransportConfig(
        proxy=config.proxy,
        cluster=config.cluster,
        bastion_host=config.bastion_host,
        bastion_user=config.bastion_user,
        tsh_path=config.tsh_path,
    )
    with pytest.raises(TransportConfigurationError):
        connect_linux("192.0.2.10", credentials, incomplete)


@patch("orbitflow.transport.linux.paramiko.ProxyCommand")
@patch("orbitflow.transport.linux.paramiko.PKey.from_path")
@patch("orbitflow.transport.linux.paramiko.SSHClient")
def test_linux_reports_bastion_failure_as_teleport_error(
    ssh_client, _from_path, proxy_command, credentials, config
):
    from orbitflow.transport import TeleportError

    bastion = ssh_client.return_value
    bastion.connect.side_effect = OSError("authentication failed")

    with pytest.raises(TeleportError) as error:
        connect_linux("192.0.2.10", credentials, config)

    assert "authentication failed" not in str(error.value)
    bastion.close.assert_called_once_with()
    proxy_command.return_value.close.assert_called_once_with()

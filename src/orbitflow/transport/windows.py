"""Windows transport using a validated tsh local TCP forward."""

from __future__ import annotations

import shutil
import socket
import subprocess
import time
from typing import Any

import paramiko

from .exceptions import DeviceConnectionError, TeleportError, TunnelError
from .models import DeviceCredentials, DeviceSession, TransportConfig


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _stop_process(process: Any) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _wait_for_tunnel(process: Any, port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise TunnelError(
                "tsh local forwarding process exited before becoming ready"
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise TunnelError("timed out waiting for the tsh local forwarding port")


def connect_windows(
    device_host: str, credentials: DeviceCredentials, config: TransportConfig
) -> DeviceSession:
    """Connect through a temporary tsh local forward on Windows."""
    tsh = config.tsh_path or shutil.which("tsh")
    if not tsh:
        raise TeleportError(
            "tsh was not found on PATH; install it and run tsh login first"
        )

    local_port = _free_local_port()
    command = [
        tsh,
        "ssh",
        "--cluster",
        config.cluster,
        "--proxy",
        config.proxy,
        "-N",
        "-L",
        f"127.0.0.1:{local_port}:{device_host}:{config.device_port}",
        f"{config.bastion_user}@{config.bastion_host}",
    ]
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise TeleportError("failed to start tsh local forwarding") from exc

    client = paramiko.SSHClient()
    forwarded_socket = None
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        _wait_for_tunnel(process, local_port, config.connect_timeout)
        # Keep the real device hostname as Paramiko's host-key lookup key while
        # sending traffic through the loopback forward.
        forwarded_socket = socket.create_connection(
            ("127.0.0.1", local_port), timeout=config.connect_timeout
        )
        client.connect(
            device_host,
            port=config.device_port,
            username=credentials.username,
            password=credentials.password,
            pkey=credentials.pkey,
            sock=forwarded_socket,
            timeout=config.connect_timeout,
        )
    except Exception as exc:
        client.close()
        if forwarded_socket is not None:
            forwarded_socket.close()
        _stop_process(process)
        if isinstance(exc, TunnelError):
            raise
        raise DeviceConnectionError(
            f"failed to connect to target device {device_host}"
        ) from exc

    def cleanup() -> None:
        try:
            client.close()
        finally:
            try:
                if forwarded_socket is not None:
                    forwarded_socket.close()
            finally:
                _stop_process(process)

    return DeviceSession(client, cleanup)

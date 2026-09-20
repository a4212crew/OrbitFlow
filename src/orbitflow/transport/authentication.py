"""Shared target-device SSH authentication helpers."""

from __future__ import annotations

from typing import Any

import paramiko

from .models import DeviceCredentials


def _password_interactive_handler(password: str):
    """Build a handler that supplies the password only to password prompts."""

    def handler(
        _title: str, _instructions: str, prompts: list[tuple[str, bool]]
    ) -> list[str]:
        if not prompts or any(
            "password" not in prompt.lower() for prompt, _ in prompts
        ):
            raise paramiko.AuthenticationException(
                "keyboard-interactive requested a non-password response"
            )
        return [password for _prompt, _echo in prompts]

    return handler


def connect_target(
    client: Any,
    device_host: str,
    credentials: DeviceCredentials,
    **connect_kwargs: Any,
) -> None:
    """Connect with normal auth, then retry a rejected password interactively."""
    password_error: paramiko.AuthenticationException | None = None
    try:
        client.connect(
            device_host,
            username=credentials.username,
            password=credentials.password,
            pkey=credentials.pkey,
            **connect_kwargs,
        )
        return
    except paramiko.AuthenticationException as exc:
        password_error = exc
        if credentials.password is None:
            raise
        allowed_types = getattr(password_error, "allowed_types", None)
        if allowed_types is not None and "keyboard-interactive" not in allowed_types:
            raise

    transport = client.get_transport()
    if transport is None or not transport.is_active():
        assert password_error is not None
        raise password_error
    transport.auth_interactive(
        credentials.username,
        _password_interactive_handler(credentials.password),
    )

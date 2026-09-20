# OrbitFlow

OrbitFlow is a multi-vendor network automation platform. This version provides
the shared SSH transport layer and a reusable Cisco IOS/IOS-XE interactive CLI;
inventory, collection, and provisioning workflows are intentionally out of scope.

## Setup

Use Python 3.11 or newer in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate          # Linux
# .venv\Scripts\Activate.ps1       # Windows PowerShell
python -m pip install -r requirements.txt
export PYTHONPATH="$PWD/src"         # Linux
# $env:PYTHONPATH = "$PWD/src"       # Windows PowerShell
```

Install `tsh` separately and authenticate interactively before running OrbitFlow:

```bash
tsh login --proxy=<teleport-proxy>
tsh status
```

OrbitFlow never performs `tsh login` or handles an OTP.

## Transport API

Callers provide routing configuration and target-device credentials explicitly;
nothing contains production credentials or user-specific paths.

```python
from pathlib import Path
from orbitflow.transport import DeviceCredentials, TransportConfig, connect_device

config = TransportConfig(
    proxy="teleport.example.net:443",
    cluster="example-cluster",
    bastion_host="example-bastion",
    bastion_user="teleport-user",
    # Required on Linux; discover these from the active tsh profile.
    teleport_key_path=Path("/path/from/active/tsh/profile/key"),
    teleport_cert_path=Path("/path/from/active/tsh/profile/key-cert.pub"),
    verify_bastion_host_key=False,  # Linux bastion; permissive by default.
    verify_device_host_key=False,  # Target device; permissive by default.
)

with connect_device(
    "192.0.2.10",
    DeviceCredentials(username="network-user", password="from-secret-provider"),
    config,
) as session:
    shell = session.invoke_shell()
```

## Cisco IOS/IOS-XE interactive CLI

`CiscoIOSCLI` uses an existing `DeviceSession`; it does not implement or bypass
the transport layer. It dynamically recognizes prompts ending in `#` or `>`,
disables paging with `terminal length 0`, and reads until each command's trailing
prompt using the requested timeout. Returned text excludes the command echo and
trailing prompt.

```python
from orbitflow.vendors.cisco import CiscoIOSCLI

with connect_device(device_host, credentials, config) as session:
    cli = CiscoIOSCLI(session, timeout=10)
    version = cli.run_command("show version", timeout=30)
```

This class is specifically for IOS and IOS-XE. Future IOS-XR behavior belongs in
a separate vendor module rather than being inferred from matching commands.

On Windows, OrbitFlow starts `tsh ssh -N -L` and connects Paramiko to the local
forward while retaining the device address for SSH host-key verification. On
Linux, it starts `tsh proxy ssh`, authenticates the bastion using the
provided Teleport private key and certificate, opens a Paramiko `direct-tcpip`
channel, and connects the target client over that channel. Resources are closed
in reverse dependency order.

Host-key verification is independently configurable for the Linux bastion and
the target device. Both `verify_bastion_host_key` and
`verify_device_host_key` default to `False`, matching the permissive host-key
handling successfully used during Windows and Linux live validation. Permissive
mode uses Paramiko's `AutoAddPolicy` and does not persist learned keys. Setting
either applicable option to `True` loads normal system host keys and uses
Paramiko's `RejectPolicy`; strict mode therefore requires the relevant host key
to have been provisioned there. OrbitFlow does not load Teleport-specific
known-host files or implement custom Teleport CA verification. Permissive mode
trades protection against machine-in-the-middle attacks for compatibility, so
enable strict verification when trusted system host keys can be provisioned.

The caller is responsible for obtaining target credentials from an approved
secret provider and for discovering the active Teleport identity paths. Passwords,
private keys, and OTPs must not be logged or committed.

## Tests

The suite uses mocks and does not contact Teleport or network devices:

```bash
PYTHONPATH=src pytest
```

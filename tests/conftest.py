"""Provide an import-only Paramiko substitute for dependency-free mock tests."""

import sys
from types import ModuleType
from unittest.mock import MagicMock


paramiko = ModuleType("paramiko")
paramiko.SSHClient = MagicMock
paramiko.RejectPolicy = MagicMock
paramiko.ProxyCommand = MagicMock


class FakePKey:
    from_path = MagicMock()


paramiko.PKey = FakePKey
sys.modules.setdefault("paramiko", paramiko)

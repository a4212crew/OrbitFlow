"""Ubiquiti EdgeSwitch vendor support."""

from .interfaces import EdgeSwitchInterfaceAdapter, parse_interfaces_status

__all__ = ["EdgeSwitchInterfaceAdapter", "parse_interfaces_status"]

"""Transport-specific exceptions exposed by OrbitFlow."""


class TransportError(Exception):
    """Base class for failures while establishing or using a transport."""


class UnsupportedPlatformError(TransportError):
    """Raised when the execution operating system is unsupported."""


class TransportConfigurationError(TransportError):
    """Raised when required, non-secret transport settings are missing."""


class TeleportError(TransportError):
    """Raised when a Teleport command or credential is unavailable."""


class TunnelError(TransportError):
    """Raised when a tunnel or forwarding channel cannot be opened."""


class DeviceConnectionError(TransportError):
    """Raised when SSH connection to the target device fails."""

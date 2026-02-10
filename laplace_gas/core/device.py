# core/device.py
from PyQt6.QtCore import QMutex, QMutexLocker
import propar


class DeviceError(RuntimeError):
    """Raised when device communication fails."""


class Device:
    """Persistent, thread-safe wrapper for a Bronkhorst device."""

    def __init__(self, port: str):
        """Open device on the given COM port."""
        self.port = port
        self._mutex = QMutex()
        try:
            self._instrument = propar.instrument(port)
        except Exception as exc:
            raise DeviceError(f"Failed to open device on port {port}") from exc

    def read(self, parameter: int):
        """Read a single parameter safely."""
        with QMutexLocker(self._mutex):
            try:
                return self._instrument.readParameter(parameter)
            except Exception as exc:
                raise DeviceError(f"Read failed (param {parameter})") from exc

    def write(self, parameter: int, value):
        """Write a single parameter safely."""
        with QMutexLocker(self._mutex):
            try:
                self._instrument.writeParameter(parameter, value)
            except Exception as exc:
                raise DeviceError(f"Write failed (param {parameter}, value {value})") from exc

    def read_many(self, *parameters: int) -> dict[int, int]:
        """Read multiple parameters safely."""
        with QMutexLocker(self._mutex):
            try:
                return {p: self._instrument.readParameter(p) for p in parameters}
            except Exception as exc:
                raise DeviceError("Read-many failed") from exc

    def write_many(self, values: dict[int, int]) -> None:
        """Write multiple parameters safely."""
        with QMutexLocker(self._mutex):
            for p, v in values.items():
                try:
                    self._instrument.writeParameter(p, v)
                except Exception as exc:
                    raise DeviceError(f"Write-many failed (param {p}, value {v})") from exc

    def close(self):
        """Close the device connection."""
        close_fn = getattr(self._instrument, "close", None)
        if callable(close_fn):
            close_fn()

"""
Device access layer.
Wraps propar.instrument with thread-safe read/write operations.
"""


from PyQt6.QtCore import QMutex, QMutexLocker
import propar


class DeviceError(RuntimeError):
    """Raised when device communication fails."""


class Device:
    def __init__(self, port: str):
        self.port = port
        self._mutex = QMutex()

        try:
            self._instrument = propar.instrument(port)
        except Exception as exc:
            raise DeviceError(f"Failed to open device on port {port}") from exc


    def read(self, parameter: int):
        """
        Thread-safe read of a propar parameter.
        """
        with QMutexLocker(self._mutex):
            try:
                return self._instrument.readParameter(parameter)
            except Exception as exc:
                raise DeviceError(f"Read failed (param {parameter})") from exc


    def write(self, parameter: int, value):
        """
        Thread-safe write to a propar parameter.
        """
        with QMutexLocker(self._mutex):
            try:
                self._instrument.writeParameter(parameter, value)
            except Exception as exc:
                raise DeviceError(
                    f"Write failed (param {parameter}, value {value})"
                ) from exc


    ### helpers

    def read_many(self, *parameters: int) -> dict[int, int]:
        """
        Read several parameters under a single lock.
        """
        return {param: self.read(param) for param in parameters}


    def write_many(self, values: dict[int, int]) -> None:
        """
        Write several parameters under a single lock.
        """
        for param, value in values.items():
            self.write(param, value)

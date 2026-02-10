# utils/get_com_port.py
import sys
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
import serial.tools.list_ports
from core.device import Device, DeviceError
from laplace_log import log


def get_com_port(config) -> str:
    """
    Detects and selects the COM port to use for the Bronkhorst device.
    1. Reads default port from config.
    2. Lists all available COM ports.
    3. Moves default port to first position if available.
    4. Shows a dialog for the user to select.
    5. Loops until a working connection is made or user cancels.
    """
    log.debug("Selecting COM port...")
    default_port = config['Connection'].get('default_com_port', '')

    app = QApplication.instance() or QApplication(sys.argv)

    while True:
        # List available ports
        available_ports = [p.device for p in serial.tools.list_ports.comports()]

        if not available_ports:
            QMessageBox.critical(None, "Connection Error",
                                 "No COM ports found. Please ensure your device is connected.")
            sys.exit(1)

        # Move default port to first position if present
        if default_port in available_ports:
            available_ports.insert(0, available_ports.pop(available_ports.index(default_port)))

        # Ask the user to select a port
        selected_port, ok = QInputDialog.getItem(
            None, "Select COM Port",
            "Connect to Bronkhorst device on:",
            available_ports, 0, False
        )

        if not ok:
            log.info("User cancelled COM port selection.")
            sys.exit(0)

        if selected_port:
            log.info(f"Attempting to connect to {selected_port}...")
            try:
                # Test the device by reading the serial number (param 1)
                device_test = Device(selected_port)
                serial_number = device_test.read(1)
                if serial_number is None:
                    raise ConnectionError("Device is not responding on this port.")
                
                log.info(f"Successfully connected to device on {selected_port}, serial: {serial_number}")
                return selected_port
            except DeviceError as e:
                log.warning(f"DeviceError on {selected_port}: {e}")
                QMessageBox.critical(
                    None,
                    "Connection Error",
                    f"Failed to connect to {selected_port}.\n\nError: {e}\nPlease try another port."
                )
                continue
            except Exception as e:
                log.warning(f"Unexpected error on {selected_port}: {e}")
                QMessageBox.critical(
                    None,
                    "Unexpected Error",
                    f"Failed to connect to {selected_port}.\n\nError: {e}\nPlease try another port."
                )
                continue

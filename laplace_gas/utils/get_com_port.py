# libraries
import sys
from configparser import ConfigParser

from laplace_log import log
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
import serial.tools.list_ports


# project
from core.device import Device, DeviceError


def get_com_port(config: ConfigParser) -> str:
    """
    Prompt the user to select a COM port and verify communication with a
    Bronkhorst device.

    The function lists available serial ports, prioritizes the default port
    from the configuration, and attempts to connect by reading the device
    serial number. The selection dialog is shown repeatedly until a working
    device is found or the user cancels.

    Returns:
        str: The validated COM port name.

    Exits:
        Exits the application if no ports are available or the user cancels.
    """
    log.debug("Selecting COM port...")
    default_port = config['Connection'].get('default_com_port', '')

    app = QApplication.instance() or QApplication(sys.argv)

    # display the window until selection
    while True:

        # List available ports
        available_ports = [p.device for p in serial.tools.list_ports.comports()]

        if not available_ports:
            QMessageBox.critical(
                None, "Connection Error",
                "No COM ports found. Please ensure your device is connected."
            )
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
                
                device_test = Device(selected_port)   # make a test device
                serial_number = device_test.read(1)   # try to acces to the serial number
                device_test.close()                   # close the test device
                
                if serial_number is None:             # if there is no serial device
                    raise ConnectionError("Device is not responding on this port.")  # the connection failed
                
                log.info(f"Device successfully connected on {selected_port}, serial: {serial_number}")

                return selected_port
            
            except (DeviceError, ConnectionError) as e: # if a connection error was raised
                log.warning(f"ConnectionError on {selected_port}: {e}")
                QMessageBox.critical(
                    None, "Connection Error",
                    f"Failed to connect to {selected_port}.\n\n"
                    f"Error: {e}\n"
                    f"Please try another port."
                )
                continue            # let the user select another port
            
            except Exception as e:  # if another error was raised
                log.warning(f"Unexpected error on {selected_port}: {e}")
                QMessageBox.critical(
                    None,
                    "Unexpected Error",
                    f"Unexpected error when trying to connect to {selected_port}.\n\n"
                    f"Error: {e}\n"
                    f"Please try another port."
                )
                continue            # let the user select another port

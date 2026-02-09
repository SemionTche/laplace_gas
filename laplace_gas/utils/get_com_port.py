import sys
from configparser import ConfigParser
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox
import serial.tools.list_ports
import propar


def get_com_port(config: ConfigParser) -> str:
    """
    Detects and selects the COM port to use for the device.
    1. Reads default port from config.
    2. Lists all available COM ports.
    3. Moves default port to first position if available.
    4. Shows a dialog for the user to select.
    5. Loops until a working connection is made or user cancels.
    """
    default_port = config['Connection'].get('default_com_port', '')

    while True:
        ports_objects = serial.tools.list_ports.comports()
        available_ports = [port.device for port in ports_objects]

        if not available_ports:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, "Connection Error",
                                 "No COM ports found. Please ensure your device is connected.")
            sys.exit(1)

        # Move default port to index 0 if present
        if default_port in available_ports:
            available_ports.insert(0, available_ports.pop(available_ports.index(default_port)))

        selected_port, ok = QInputDialog.getItem(
            None, "Select COM Port",
            "Connect to Bronkhorst device on:",
            available_ports, 0, False
        )

        if not ok:  # user canceled
            print("No valid port selected. Exiting application.")
            sys.exit()

        if selected_port:
            print(f"Attempting to connect to {selected_port}...")
            try :
                device_test = propar.instrument(selected_port)
                serial_test = device_test.readParameter(1) # Try to read the serial number
                
                if serial_test is None:
                    print("Device is not responding on this port.")
                    continue
                
                print(f"Successfully connected to device with serial number: {serial_test}")

                return selected_port

            except Exception as e: # If connection fails, show an error
                print("Connection failed.")
                QMessageBox.critical(
                    None, 
                    "Connection Error",
                    f"Failed to connect to {selected_port}.\n\n"
                    f"Error: {e}\n\n"
                    f"Please check connection or try another port."
                )
                continue
# libraries
import sys
import logging

from laplace_log.log_lhc import LoggerLHC, log
from laplace_server.protocol import LOGGER_NAME

LoggerLHC("laplace.gas", file_level="debug", console_level="info")
log.info("Starting OptWindow...")

logging.getLogger(LOGGER_NAME).setLevel(logging.INFO)

from PyQt6.QtWidgets import QApplication
import qdarkstyle

# project
from utils.get_config import load_configuration
from utils.get_com_port import get_com_port
from core.device import Device
from interface.gasWindow import GasWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    config = load_configuration()
    port = get_com_port(config)

    device = Device(port)
    
    window = GasWindow(device, config)
    window.show()

    # controller = Controller(device, config)

    # end the process
    exit_code = app.exec()
    log.info(f"Application is exiting with code {exit_code}.")
    sys.exit(exit_code)
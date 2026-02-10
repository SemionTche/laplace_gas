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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    config = load_configuration()
    port = get_com_port(config)

    device = Device(port)
    print("passed")
    # controller = Controller(device, config)

    # window = MainWindow(controller, config)
    # window.show()

    sys.exit(app.exec())
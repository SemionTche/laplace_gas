import sys

from PyQt6.QtWidgets import QApplication
import qdarkstyle

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())

    config = load_configuration()
    port = select_com_port(config)

    device = Device(port)
    controller = Controller(device, config)

    window = MainWindow(controller, config)
    window.show()

    sys.exit(app.exec())
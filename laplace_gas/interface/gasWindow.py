# libraries
from configparser import ConfigParser
import pathlib

from PyQt6.QtWidgets import QMainWindow
from PyQt6.uic import loadUi

# project
from core.controller import FlowController
from core.device import Device

class GasWindow(QMainWindow):
    
    def __init__(self, device: Device, config: ConfigParser):
        super().__init__()

        self.device = device
        self.config = config
        self.controller = FlowController(device, config)

        p = pathlib.Path(__file__)

        loadUi(str(p.parent / "flow.ui"), self)

        # self._setup_ui()
        # self._setup_connections()
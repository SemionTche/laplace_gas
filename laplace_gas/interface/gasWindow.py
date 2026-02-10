# libraries
from configparser import ConfigParser
import pathlib
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QButtonGroup
)
from PyQt6.QtCore import QTimer
from PyQt6.uic import loadUi

from laplace_log import log

# project
from core.controller import FlowController
from core.device import Device
from utils.qt_logging_bridge import QtLogHandler


__version__ = "2.0.0-beta"



class GasWindow(QMainWindow):
    
    def __init__(self, device: Device, config: ConfigParser):
        super().__init__()

        self.device = device
        self.config = config

        p = pathlib.Path(__file__)
        self.win = loadUi(str(p.parent / "flow.ui"), self)



        self.is_offline = False
        self.connection_successful = False

        # Initialize plot_window to None to prevent AttributeError if connection fails
        self.plot_window = None

        self.setup()


    def setup(self):
        self.setup_logs()
        self.controller = FlowController(self.device, self.config)
        self.setup_controls()
    

    def setup_logs(self):
        ### REDIRECT PRINT STATEMENTS
        qt_handler = QtLogHandler()
        logging.getLogger().addHandler(qt_handler)
        qt_handler.new_log.connect(self.update_log)

        log.info(f"--- LOA Pressure Control v{__version__} ---")


    def setup_controls(self):
        
        ### GROUPING RADIO BUTTONS
            # This ensures they are mutually exclusive and easier to manage
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.win.radioPID)
        self.mode_group.addButton(self.win.radioShut)

            # Set ID for easier logic later (1=PID, 0=Shut)
        self.mode_group.setId(self.win.radioPID, 1)
        self.mode_group.setId(self.win.radioShut, 0)


        self.win.setpoint.setGroupSeparatorShown(False)

        ### Flickering Label
        self.flicker_timer = QTimer(self)
        self.label_is_visible = True  # State tracker for the flicker
        self.flicker_timer.timeout.connect(self._toggle_status_label_visibility)
        
        self.controller.purge_finalized.connect(self.win.radioShut.isChecked)

        # self.controller.alarm_triggered.connect(self._on_alarm_triggered)

    
    def _toggle_status_label_visibility(self):
        """Toggles the stylesheet of the status label to make it flicker. """
        if self.label_is_visible:
            # Make text transparent (same as background)
            self.win.label_valve_status.setStyleSheet("color: transparent;")
        else:
            self.win.label_valve_status.setStyleSheet("color: red;")

        # Flip the state for the next tick
        self.label_is_visible = not self.label_is_visible


    def update_log(self, text):
        """Appends text to the QTextEdit."""
        self.win.log_display.append(text)
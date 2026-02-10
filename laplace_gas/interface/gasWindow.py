# libraries
from configparser import ConfigParser
import pathlib
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QButtonGroup, QMessageBox, QRadioButton
)
from PyQt6.QtCore import QTimer
from PyQt6.uic import loadUi

from laplace_log import log

# project
from core.controller import FlowController
from core.device import Device
# from utils.qt_logging_bridge import QtLogEmitter


import logging
from utils.qt_logging_bridge import QtLogHandler#, QtLogEmitter




class GasWindow(QMainWindow):
    
    def __init__(self, device: Device, config: ConfigParser):
        super().__init__()

        self.device = device
        self.config = config
        self.controller = FlowController(device, config)

        p = pathlib.Path(__file__)

        self.win = loadUi(str(p.parent / "flow.ui"), self)

        self.is_offline = False
        self.connection_successful = False

        self.setup()


    def setup(self):
        self.setup_controls()
    

    def setup_controls(self):
        # --- GROUPING RADIO BUTTONS ---
        # This ensures they are mutually exclusive and easier to manage
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.win.radioPID)
        self.mode_group.addButton(self.win.radioShut)

        # Set ID for easier logic later (1=PID, 0=Shut)
        self.mode_group.setId(self.win.radioPID, 1)
        self.mode_group.setId(self.win.radioShut, 0)

        self.win.setpoint.setGroupSeparatorShown(False)

        # Initialize plot_window to None to prevent AttributeError if connection fails
        self.plot_window = None

        # -----Flickering Label-----------
        self.flicker_timer = QTimer(self)
        self.flicker_timer.timeout.connect(self._toggle_status_label_visibility)
        self.label_is_visible = True  # State tracker for the flicker
        
        self.controller.purge_finalized.connect(self.win.radioShut.isChecked)
        # self.win.radioShut.toggled.connect(self.controller.purge_finalized)

        # self.controller.alarm_triggered.connect(self._on_alarm_triggered)

        # --- REDIRECT PRINT STATEMENTS ---
        qt_handler = QtLogHandler()
        # qt_log_emitter = QtLogEmitter()

        # qt_handler = QtLogHandler(qt_log_emitter)
        # qt_handler.setFormatter(logging.Formatter(
        #     "%(asctime)s [%(levelname)s] %(message)s"
        # ))

        logging.getLogger().addHandler(qt_handler)
        # qt_log = QtLogEmitter(logging.INFO)
        # qt_log.log_signal.connect(self.update_log)
        # qt_log_emitter.log_received.connect(self.update_log)
        qt_handler.new_log.connect(self.update_log)
        print("hi")
        log.debug("debug")
        log.info("info")
        log.warning("warning")
        log.error("error")
        # self.log_stream = Stream()
        # self.log_stream.new_text.connect(self.update_log)
        # sys.stdout = self.log_stream
        # print(f"--- LOA Pressure Control v{__version__} ---")

    
    def _toggle_status_label_visibility(self):
        """ Toggles the stylesheet of the status label to make it flicker. """
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
        # cursor = self.win.log_display.textCursor()
        # cursor.movePosition(cursor.End)
        # cursor.insertText(text)
        # self.win.log_display.setTextCursor(cursor)
        # self.win.log_display.ensureCursorVisible()
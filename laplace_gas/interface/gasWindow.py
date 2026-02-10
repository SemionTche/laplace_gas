# libraries
from configparser import ConfigParser
import pathlib

from PyQt6.QtWidgets import (
    QMainWindow, QButtonGroup
)
from PyQt6.QtCore import QTimer
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

        # --- Alarm Cooldown Timer ---
        self.rearm_timer = QTimer(self)
        self.rearm_timer.setSingleShot(True)
        self.rearm_timer.timeout.connect(self._reenable_alarm)
        self.last_known_setpoint = 0.0  # Track previous setpoint
        self.lower_setpoint_cooldown = 2.0  # Default value, updated later from config
        #self.was_last_change_decrease = False
        self.is_purging = False
        self.instrument_mutex = QMutex()

        self.purge_target = 0.0  # Default target
        self.purge_timeout_limit = 10.0  # Default timeout

        self.current_pressure_bar = 0.0  # Stores the latest reading
        self.purge_target = 0.0          # Stores target for check
        self.purge_check_timer = QTimer(self)
        self.purge_check_timer.timeout.connect(self._check_purge_condition)
        self.purge_start_time = 0.0
    

    def _toggle_status_label_visibility(self):
        """ Toggles the stylesheet of the status label to make it flicker. """
        if self.label_is_visible:
            # Make text transparent (same as background)
            self.win.label_valve_status.setStyleSheet("color: transparent;")
        else:
            self.win.label_valve_status.setStyleSheet("color: red;")

        # Flip the state for the next tick
        self.label_is_visible = not self.label_is_visible
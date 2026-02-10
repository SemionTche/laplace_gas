import time
from configparser import ConfigParser
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QMutex

from laplace_log import log

from core.device import Device


class FlowController(QObject):
    purge_finalized = pyqtSignal(bool)

    def __init__(self, device: Device, config: ConfigParser):
        super().__init__()
        self.device = device
        self.config = config

        log.info("Reading initial device status...")
        initial_status = self.device.read(28)
        if initial_status is not None:
            binary_string = bin(initial_status)[2:].zfill(8)
            log.info(f"Initial device status (param 28): Value={initial_status}, Bits={binary_string}")
        else:
            log.warning("Could not read initial device status.")

        # --- Alarm Cooldown Timer ---
        self.rearm_timer = QTimer(self)
        self.rearm_timer.setSingleShot(True)
        self.rearm_timer.timeout.connect(self._reenable_alarm)
        self.last_known_setpoint = 0.0      # Track previous setpoint
        self.lower_setpoint_cooldown = 2.0  # Default value, updated later from config
        self.is_purging = False


        self.instrument_mutex = QMutex()


        self.purge_target = 0.0          # Default target
        self.purge_timeout_limit = 10.0  # Default timeout

        self.current_pressure_bar = 0.0  # Stores the latest reading
        self.purge_target = 0.0          # Stores target for check
        self.purge_check_timer = QTimer(self)
        self.purge_check_timer.timeout.connect(self._check_purge_condition)
        self.purge_start_time = 0.0


    def read_device_info(self):
        capacity = self.device.read(21)
        unit = self.device.read(129)

        self.capacity = float(capacity)
        print(f"Device Capacity Read: {self.capacity}")
        self.unit = str(unit).strip()
        print(f"Device Unit Read: '{self.unit}'")

        return self.capacity, self.unit


    def get_effective_max_pressure(self) -> float:
        if self.capacity is None:
            raise RuntimeError("Capacity not read")

        safety_limit = self.config['Safety'].getfloat(
            'max_set_pressure', self.capacity
        )
        return min(self.capacity, safety_limit)
    

    def normalize_user_tag(self, raw) -> str:
        if raw is None:
            return ""

        if isinstance(raw, (bytes, bytearray)):
            return raw.decode('utf-8', errors='ignore')

        return str(raw)
    


    def _reenable_alarm(self):
        """
        Re-enables the alarm if PID mode is still active.
        Checks if pressure is actually safe before arming.
        """
        # 1. If Purging, do nothing (Purge logic owns the alarm state)
        if self.is_purging:
            return

        # 2. If Alarm is supposed to be on...
        if self.valve_status == "PID" and self.response_alarm_enabled:

            # --- SMART CHECK ---
            # Calculate where the alarm WOULD trigger (Setpoint + Tolerance)
            current_limit = self.win.setpoint.value() + self.safety_tolerance_bar

            # If we are still above that limit, DO NOT enable alarm. Wait again.
            if self.current_pressure_bar > current_limit:
                print(f"Cooldown Check: Pressure ({self.current_pressure_bar:.2f}) > "
                      f"Limit ({current_limit:.2f}). Extending wait...")

                # Restart the timer for another cycle (e.g. another 5 seconds)
                # This gives the physics time to catch up
                self.rearm_timer.start(int(self.lower_setpoint_cooldown * 1000))
                return
            # -------------------

            try:
                print("Cooldown finished & Pressure Safe: Re-enabling Safety Alarm (Mode 2)")
                self.instrument_mutex.lock()
                try:
                    self.instrument.writeParameter(118, 2)
                finally:
                    self.instrument_mutex.unlock()
            except Exception as e:
                print(f"Failed to re-enable alarm: {e}")
    

    def _check_purge_condition(self):
        """
        Called repeatedly by purge_check_timer.
        Checks if pressure is close to target or if timeout has passed.
        """
        # Define "Close enough" (e.g., +/- 0.5 bar)
        TOLERANCE = 1.5

        elapsed = time.time() - self.purge_start_time
        current_diff = abs(self.current_pressure_bar - self.purge_target)

        # 1. SUCCESS CONDITION: Pressure is within tolerance
        if current_diff <= TOLERANCE:
            log.debug(f"Purge Target Reached! (Diff: {current_diff:.4f} bar). Closing.")
            self._finalize_purge()

        # 2. TIMEOUT CONDITION: Time exceeded limit
        elif elapsed >= self.purge_timeout_limit:
            log.debug(f"Purge Timeout ({elapsed:.1f}s > {self.purge_timeout_limit}s). Forcing Close.")
            self._finalize_purge()

        # 3. Otherwise, do nothing and wait for next timer tick
    

    def _finalize_purge(self):
        """
        Stops the timer and closes the valves.
        """
        # Stop the checking timer so it doesn't fire again
        if self.purge_check_timer.isActive():
            self.purge_check_timer.stop()
        self.is_purging = False
        log.debug("Purge Sequence Complete. Closing valves.")

        # Close the valve
        self.valve_close()

        # Ensure the UI Radio Button reflects the change
        self.purge_finalized.emit(True)
        
    

    def valve_close(self):
        log.debug('Valve closed')
        self.win.label_valve_status.setText('Shut')

        self.flicker_timer.start(500)  # 500 ms interval
        self.instrument_mutex.lock()  # <--- Lock
        try:
            self.instrument.writeParameter(12, 3)  # 'Valve Closed' command
        finally:
            self.instrument_mutex.unlock()
        self.valve_status = "closed"

        # --- Disable Alarm ---
        try:
            self.instrument_mutex.lock()  # <--- Lock
            try:
                self.instrument.writeParameter(118, 0)
            finally:
                self.instrument_mutex.unlock()
            print("Safety Alarm: DISABLED (Mode 0)")
        except Exception as e:
            print(f"Failed to disable alarm: {e}")
        # --------------------------

        if hasattr(self.win, 'inlet_valve_label'):
            self.win.inlet_valve_label.setStyleSheet("color: gray;")
            self.win.inlet_valve_label.setText("...")
        if hasattr(self.win, 'label_In_Out'):
            self.win.label_In_Out.setStyleSheet("color: gray;")
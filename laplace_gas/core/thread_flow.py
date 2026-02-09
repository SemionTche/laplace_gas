import time
from PyQt6.QtCore import QThread, pyqtSignal
from laplace_log import log

# project
from core.conversions import valve_raw_to_percent
from core.device import Device, DeviceError

class ThreadFlow(QThread):
    """
    Thread handling periodic device reads and flow regulation.
    """

    # ---- Signals (unchanged) ----
    pressure_signal = pyqtSignal(float, float)  # time, pressure
    valve_signal = pyqtSignal(float)
    alarm_signal = pyqtSignal(str)
    critical_alarm = pyqtSignal(int)
    purge_signal = pyqtSignal(bool)

    def __init__(self,
                 device: Device,
                 config,
                 sleep_time: float,
                 parent=None,):
        
        super().__init__(parent)
        
        # ---- Injected dependencies ----
        self.device = device
        self.config = config
        self.sleep_time = sleep_time
        self.main = parent

        self._running = False

        self.capacity = getattr(parent, "capacity", None)
        self.propar_to_bar_func = getattr(parent, "propar_to_bar_func", None)


    def run(self):
        self._running = True
        last_alarm_status = 0  # Track changes

        while self._running:

            # 1. Mark the start time of this cycle
            loop_start_time = time.time()

            try:

                values = self.device.read_many(28, 8, 55)
                alarm_status = values[28]
                raw_measure = values[8]
                valve1_output = values[55]
                
                # ---- Offline detection ----
                if raw_measure is None:  # If critical read fails (None), device is disconnected.
                    self.alarm_signal.emit("offline") # If offline, don't do drift calculation, just wait 1s and retry
                    time.sleep(1.0)
                    continue


                # ---- Alarm logic ----
                if alarm_status is not None and alarm_status != last_alarm_status:
                    print(
                        f"[ALARM CHANGE] Status Code: {alarm_status} "
                        f"(Binary: {bin(alarm_status)})"
                    )
                    last_alarm_status = alarm_status

                    if alarm_status & 1:
                        self.alarm_signal.emit('Error')
                    elif alarm_status & 2:
                        self.alarm_signal.emit('Warning')
                    else:
                        self.alarm_signal.emit('Normal')

                    if (alarm_status & 32) or (alarm_status & 8):
                        self.critical_alarm.emit(alarm_status)


                # --- Emission Logic (Pressure) ---
                timestamp = time.time()
                bar_measure = self.propar_to_bar_func(raw_measure, self.capacity)
                self.MEAS.emit(timestamp, bar_measure)

                # ---- Pressure emission ----
                timestamp = time.time()  # We use the current time as the timestamp for the graph
                bar_measure = self.propar_to_bar_func(raw_measure, self.capacity)
                self.pressure_signal.emit(timestamp, bar_measure)

                # ---- Valve emission ----
                if valve1_output is not None:
                    # Ensure the helper function is accessible here
                    valve_percent = valve_raw_to_percent(valve1_output)
                    self.valve_signal.emit(valve_percent)

                # ---- Drift-corrected sleep ----
                work_duration = time.time() - loop_start_time                
                # Compute remaining time to match the configured thread_sleep_time
                remaining = self.sleep_time - work_duration
                if remaining > 0:
                    time.sleep(remaining)
                else:
                    log.warning(f"The reading process is slower than the config time allowed.")

            except DeviceError as exc:
                print(f"Device error: {exc}")
                self.alarm_signal.emit("offline")
                time.sleep(2.0) # On exception, wait a safe fixed amount before retrying
            
            except Exception as exc:
                print(f"Unexpected thread error: {exc}")
                time.sleep(2.0)

        print('Measurement thread stopped.')


    def stopThread(self):
        self._running  = True

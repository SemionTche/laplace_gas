import time
from PyQt6.QtCore import QThread, pyqtSignal

# project
from core.conversions import valve_raw_to_percent

class ThreadFlow(QThread):
    """
    Thread handling periodic device reads and flow regulation.
    """

    # ---- Signals (unchanged) ----
    pressure_signal = pyqtSignal(float)
    valve_signal = pyqtSignal(float)
    alarm_signal = pyqtSignal(str)
    purge_signal = pyqtSignal(bool)

    def __init__(self,
                 device,
                 config,
                 sleep_time: float,
                 parent=None,):
        
        super().__init__(parent)
        
        # ---- Injected dependencies ----
        self.device = device
        self.config = config
        self.sleep_time = sleep_time
        self.main = parent


    def run(self):
        last_alarm_status = 0  # Track changes
        while not self.stop:
            # 1. Mark the start time of this cycle
            loop_start_time = time.time()

            try:
                # ACQUIRE LOCK BEFORE READING
                self.parent.instrument_mutex.lock()

                try:
                    # --- Perform all reads ---
                    # This is the "Work" that causes latency (e.g., takes 0.05s)
                    alarm_status = self.instrument.readParameter(28)
                    raw_measure = self.instrument.readParameter(8)
                    valve1_output = self.instrument.readParameter(55)
                finally:
                    self.parent.instrument_mutex.unlock()
                # --- Offline Logic ---
                # If critical read fails (None), device is disconnected.
                if raw_measure is None:
                    self.DEVICE_STATUS_UPDATE.emit('offline')
                    # If offline, don't do drift calculation, just wait 1s and retry
                    time.sleep(1.0)
                    continue

                # --- Status Logic ---
                if alarm_status is not None:
                    # DEBUG: Print only if status changes or is critical
                    if alarm_status != last_alarm_status:
                        print(f" [ALARM CHANGE] Status Code: {alarm_status} (Binary: {bin(alarm_status)})")
                        last_alarm_status = alarm_status

                    if alarm_status & 1:
                        self.DEVICE_STATUS_UPDATE.emit('Error')
                    elif alarm_status & 2:
                        self.DEVICE_STATUS_UPDATE.emit('Warning')
                    else:
                        self.DEVICE_STATUS_UPDATE.emit('Normal')

                    if (alarm_status & 32) or (alarm_status & 8):
                        self.CRITICAL_ALARM.emit(alarm_status)
                # --- Emission Logic (Pressure) ---
                # We use the current time as the timestamp for the graph
                timestamp = time.time()
                bar_measure = self.propar_to_bar_func(raw_measure, self.capacity)
                self.MEAS.emit(timestamp, bar_measure)

                # --- Emission Logic (Valve) ---
                if valve1_output is not None:
                    # Ensure the helper function is accessible here
                    current_valve_value = valve_raw_to_percent(valve1_output)
                    self.VALVE1_MEAS.emit(current_valve_value)

                # --- SMART SLEEP (Drift Correction) ---
                # 1. Calculate how long the read/emit process took
                work_duration = time.time() - loop_start_time
                # 4. PRINT IT (Temporary Debug)
                #print(f"Hardware IO took: {work_duration:.4f} seconds")
                # 2. Calculate remaining time to match the configured thread_sleep_time
                sleep_time = self.thread_sleep_time - work_duration

                # 3. Only sleep if we have time left.
                # If work_duration > thread_sleep_time, the hardware is slower than the config,
                # so we run immediately without sleeping.
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                self.DEVICE_STATUS_UPDATE.emit('offline')
                print(f"Error reading from instrument: {e}")
                # On exception, wait a safe fixed amount before retrying
                time.sleep(2.0)

        print('Measurement thread stopped.')

    def stopThread(self):
        self.stop = True

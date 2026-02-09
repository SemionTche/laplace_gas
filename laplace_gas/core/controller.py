
from core.device import Device
from core.conversions import bar_to_propar

class FlowController:
    def __init__(self, device: Device, config):
        self.device = device
        self.config = config

        self.capacity = None
        self.unit = None

        self.valve_mode = "closed"   # "PID" or "closed"
        self.response_alarm_enabled = False


    def read_device_info(self):
        capacity = self.device.read(21)
        unit = self.device.read(129)

        self.capacity = float(capacity)
        print(f"Device Capacity Read: {self.capacity}")
        self.unit = str(unit).strip()
        print(f"Device Unit Read: '{self.unit}'")

        return self.capacity, self.unit


    def set_pid_mode(self):
        self.device.write(12, 0)
        self.valve_mode = "PID"


    def close_valve(self):
        self.device.write(12, 3)
        self.device.write(118, 0)  # disable alarm
        self.valve_mode = "closed"


    def set_setpoint_bar(self, value_bar: float):
        if self.capacity is None:
            raise RuntimeError("Device capacity unknown")

        raw = bar_to_propar(value_bar, self.capacity)
        self.device.write(9, raw)

        if self.valve_mode == "PID":
            self.device.write(12, 0)


    def configure_response_alarm(self):
        enable = self.config['Safety'].getboolean(
            'set_point_above_safety_enable', True
        )
        self.response_alarm_enabled = enable

        if not enable:
            self.device.write(118, 0)
            return

        tol_bar = self.config['Safety'].getfloat(
            'set_point_above_tolerance', 2.0
        )
        delay = self.config['Safety'].getint(
            'set_point_above_delay', 2
        )

        tol_raw = bar_to_propar(tol_bar, self.capacity)

        self.device.write_many({
            118: 0,          # disable first
            116: tol_raw,    # above deviation
            117: 32000,      # below ignore
            120: 1,          # enable setpoint change
            182: delay,
            118: 2           # re-enable
        })


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
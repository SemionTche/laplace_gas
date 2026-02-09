
def propar_to_bar(propar_value, capacity):
    """Converts a raw Propar value (0-32000) to the absolute unit (bar)."""
    if propar_value is None or capacity == 0:
        return 0.0
    return (float(propar_value) / 32000.0) * capacity


def bar_to_propar(bar_value, capacity):
    """Converts an absolute unit (bar) to a raw Propar value (0-32000)."""
    if bar_value is None or capacity == 0:
        return 0
    propar_float = (bar_value / capacity) * 32000.0
    return int(max(0.0, min(32000.0, propar_float)))


def valve_raw_to_percent(raw_valve_output: int) -> float:
    """Convert raw valve output (param 55) to percentage."""
    max_val = 16_777_215  # 24-bit max
    scaling = 100 * (100 / 61.67)
    return scaling * (raw_valve_output / max_val)


def valve_percent_to_raw(percent: float) -> int:
    """
    Convert valve opening percentage back to raw value.

    Mainly useful for testing or future control modes.
    """
    max_val = 16_777_215
    scaling = 100 * (100 / 61.67)
    raw = int((percent / scaling) * max_val)
    return max(0, min(max_val, raw))
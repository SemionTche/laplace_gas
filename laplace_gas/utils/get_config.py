# libraries
from pathlib import Path
from configparser import ConfigParser


def load_configuration() -> ConfigParser:
    """
    Load the application's configuration from 'config.ini'.

    If the file exists next to the main project, it is read; 
    otherwise, default settings are used and a new 'config.ini' is created.

    Returns:
        ConfigParser: Loaded configuration object.
    """
    config = ConfigParser()  # creat the config instance

    # config.ini lives next to main.py
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "config.ini"

    # default configuration
    defaults = {
        'Connection': {'default_com_port': 'COM1'},
        'Safety': {
            'max_set_pressure': '100.0',
            'set_point_above_tolerance': '1',
            'set_point_above_delay': '2',
            'set_point_above_safety_enable': '1',
            'purge_shut_delay_timeout': '7'
        },
        'Thread': {'thread_sleep_time': '0.2'},
        'Plotting': {
            'max_history': '24000',
            'default_duration': '10',
        },
        'Security': {'admin_password': 'appli'},
        'UI': {'window_title': 'LOA Pressure Control'}
    }

    if config_path.exists():        # if the path exists
        config.read(config_path)    # load the config found
    
    else:                           # else
        config.read_dict(defaults)  # consider the default one
        
        config_path.write_text("")        # ensure file exists
        with config_path.open("w") as f:  # write the default config inside
            config.write(f)

    return config

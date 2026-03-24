from typing import Optional
import numbers
from threading import Lock

from telemetrix_esp32 import telemetrix_esp32
from pymodaq_plugins_arduino.hardware.arduino_telemetrix import Arduino

lock = Lock()

class ArduinoWifi(Arduino, telemetrix_esp32.TelemetrixEsp32):
    """Arduino

    """
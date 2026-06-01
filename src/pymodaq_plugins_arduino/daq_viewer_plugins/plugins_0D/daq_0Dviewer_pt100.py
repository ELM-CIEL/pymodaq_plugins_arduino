from typing import Optional

import numpy as np
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.hardware.sensors.max31865.esp32_telemetrix_max31865 import MAX31865
from pymodaq_plugins_arduino.utils import Config

config = Config()


class DAQ_0DViewer_PT100(DAQ_Viewer_base):
    """Plugin PyMoDAQ pour la lecture de température via MAX31865 et sonde PT100.

    Broches SPI Nano ESP32 :
        SCK  → D13 = GPIO48
        MISO → D12 = GPIO47
        MOSI → D11 = GPIO38
        CS   → D10 = GPIO21
    """
    _controller_units = '°C'

    params = comon_parameters + [
        {'title': 'IP Address:', 'name': 'ip_address', 'type': 'str',
         'value': config('esp32', 'ip_address')},
    ]

    def ini_attributes(self):
        self.controller: Optional[ArduinoWifi] = None
        self.max31865: Optional[MAX31865] = None
from typing import Optional

import numpy as np
from pymodaq.utils.data import DataFromPlugins, DataToExport
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.hardware.sensors.max31865.spi_max31865 import MAX31865
from pymodaq_plugins_arduino.utils import Config

config = Config()


class DAQ_0DViewer_PT100(DAQ_Viewer_base):
    """Plugin PyMoDAQ pour la lecture de température via MAX31865 et sonde PT100.

    Les broches SPI sont configurables depuis l'interface PyMoDAQ
    ou depuis le fichier config_template.toml :
    """
    _controller_units = '°C'

    params = comon_parameters + [
        {'title': 'Connexion', 'name': 'connection', 'type': 'group', 'children': [
            {'title': 'IP Address:', 'name': 'ip_address', 'type': 'str',
             'value': config('esp32', 'ip_address')},
        ]},
        {'title': 'SPI Pins (GPIO)', 'name': 'spi_pins', 'type': 'group', 'children': [
            {'title': 'SCK pin:', 'name': 'sck_pin', 'type': 'int',
             'value': config('max31865', 'sck_pin'),
             'tip': 'Nano ESP32 legacy : D13 = GPIO48'},
            {'title': 'MISO pin:', 'name': 'miso_pin', 'type': 'int',
             'value': config('max31865', 'miso_pin'),
             'tip': 'Nano ESP32 legacy : D12 = GPIO47'},
            {'title': 'MOSI pin:', 'name': 'mosi_pin', 'type': 'int',
             'value': config('max31865', 'mosi_pin'),
             'tip': 'Nano ESP32 legacy : D11 = GPIO38'},
            {'title': 'CS pin:', 'name': 'cs_pin', 'type': 'int',
             'value': config('max31865', 'cs_pin'),
             'tip': 'Nano ESP32 legacy : D10 = GPIO21'},
        ]},
    ]

    def ini_attributes(self):
        self.controller: Optional[ArduinoWifi] = None
        self.max31865: Optional[MAX31865] = None

    def ini_detector(self, controller=None):
        self.ini_detector_init(slave_controller=controller)
        if self.is_master:
            self.controller = ArduinoWifi(
                ip_address=self.settings['connection', 'ip_address']
            )
        self.max31865 = MAX31865(
            controller=self.controller,
            sck_pin=self.settings['spi_pins', 'sck_pin'],
            miso_pin=self.settings['spi_pins', 'miso_pin'],
            mosi_pin=self.settings['spi_pins', 'mosi_pin'],
            cs_pin=self.settings['spi_pins', 'cs_pin'],
        )
        self.max31865.ini_max31865()
        info = "PT100 ready"
        initialized = True
        return info, initialized

    def close(self):
        if self.is_master:
            self.controller.shutdown()

    def grab_data(self, Naverage=1, **kwargs):
        temperature = self.max31865.get_temperature()
        self.dte_signal.emit(DataToExport(
            name='PT100',
            data=[DataFromPlugins(
                name='Temperature',
                data=[np.array([temperature])],
                dim='Data0D',
                labels=['Temperature (°C)']
            )]
        ))

    def commit_settings(self, param: Parameter):
        pass

    def stop(self):
        pass


if __name__ == '__main__':
    main(__file__)
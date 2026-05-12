from typing import Optional
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun, main,
                                                          DataActuatorType, DataActuator)
from pymodaq_gui.parameter import Parameter
from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.utils import Config

config = Config()

class DAQ_Move_FanHeater(DAQ_Move_base):
    """Plugin PyMoDAQ pour le contrôle du chauffage et du ventilateur
    via XY-MOS PWM sur ESP32 en WiFi (Telemetrix).
    Broches ESP32 :
        Chauffage   → GPIO18
        Ventilateur → GPIO17
    """
    _controller_units = '%'
    is_multiaxes = True
    _axis_names = {
        'Heater': config('esp32', 'pins', 'heater_pin'),
        'Fan': config('esp32', 'pins', 'fan_pin'),
    }
    _epsilon = 0.1
    data_actuator_type = DataActuatorType['DataActuator']

    params = [
                 {'title': 'IP Address:', 'name': 'ip_address', 'type': 'str',
                  'value': config('esp32', 'ip_address')}
             ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: Optional[ArduinoWifi] = None


if __name__ == '__main__':
    main(__file__)




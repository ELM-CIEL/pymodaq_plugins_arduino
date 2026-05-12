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

    def ini_stage(self, controller=None):
        self.controller = self.ini_stage_init(
            old_controller=controller,
            new_controller=None)
        if self.is_master:
            self.controller = ArduinoWifi(
                ip_address=self.settings['ip_address']
            )
            self.set_pins()
        info = "Heater and Fan ready"
        initialized = True
        return info, initialized

    def set_pins(self):
        for pin in self._axis_names.values():
            self.controller.set_pin_mode_analog_output(pin)

    def ini_stage(self, controller=None):
        self.controller = self.ini_stage_init(
            old_controller=controller,
            new_controller=None)
        if self.is_master:
            self.controller = ArduinoWifi(
                ip_address=self.settings['ip_address']
            )
            self.set_pins()
        info = "Heater and Fan ready"
        initialized = True
        return info, initialized

    def set_pins(self):
        for pin in self._axis_names.values():
            self.controller.set_pin_mode_analog_output(pin)

    def get_actuator_value(self):
        pos = DataActuator(data=self.controller.get_output_pin_value(self.axis_value))
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        if self.is_master:
            self.controller.set_pins_output_to(0)
            self.controller.shutdown()

    def commit_settings(self, param: Parameter):
        pass

    def move_abs(self, value: DataActuator):
        value = self.check_bound(value)
        self.target_value = value
        value = self.set_position_with_scaling(value)
        pwm_value = int(value.value() * 255 / 100)
        self.controller.analog_write_and_memorize(self.axis_value, pwm_value)

    def move_rel(self, value: DataActuator):
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)
        pwm_value = int(self.target_value.value() * 255 / 100)
        self.controller.analog_write_and_memorize(self.axis_value, pwm_value)

    def move_home(self):
        self.controller.analog_write_and_memorize(self.axis_value, 0)

    def stop_motion(self):
        pass

if __name__ == '__main__':
    main(__file__)




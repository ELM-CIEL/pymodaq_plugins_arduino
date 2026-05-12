"""
PyMoDAQ DAQ_Move plugin – Fan (and Heater) PWM control via ESP32 + XY-MOS MOSFET.

Hardware
--------
- Arduino Nano ESP32 running Telemetrix4Esp32WIFI firmware
- 2× XY-MOS 15A MOSFET modules driven from ESP32 GPIO pins
- Fan  → D8  (GPIO 17), MOSFET channel 0
- Heat → D9  (GPIO 18), MOSFET channel 1
- Communication: Wi-Fi TCP

Note on Windows
---------------
The *threaded* BLE API of telemetrix-esp32 is NOT compatible with Windows.
This plugin uses the asyncio API exclusively (via esp32_telemetrix.ESP32).

Plugin axes
-----------
- "Fan"    : PWM duty cycle 0-255 (maps to 0-100 % fan speed via MOSFET)
- "Heater" : PWM duty cycle 0-255 (maps to 0-100 % heater power via MOSFET)

Both axes share a single ESP32 controller (master/slave pattern).
"""

from typing import Optional

from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base,
    comon_parameters_fun,
    main,
    DataActuatorType,
    DataActuator,
)
from pymodaq_utils.utils import ThreadCommand
from pymodaq_gui.parameter import Parameter

# Import the synchronous ESP32 wrapper (place esp32_telemetrix.py inside
# src/pymodaq_plugins_arduino/hardware/)
from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ESP32

# ---------------------------------------------------------------------------
# Pin mapping  (Arduino Nano ESP32 silk-screen → GPIO number)
#   D8  = GPIO 17   ← Fan MOSFET TRIG
#   D9  = GPIO 18   ← Heater MOSFET TRIG
# ---------------------------------------------------------------------------
_FAN_PIN = 17
_HEATER_PIN = 18

# Each PWM channel on the ESP32 must be unique (0-15)
_PIN_CHANNEL = {
    _FAN_PIN: 0,
    _HEATER_PIN: 1,
}

# Default IP / port – can be overridden from the PyMoDAQ settings panel
_DEFAULT_IP = "172.17.50.234"
_DEFAULT_PORT = 31336


class DAQ_Move_Fan(DAQ_Move_base):
    """
    PyMoDAQ actuator plugin controlling a fan and a heater via PWM through
    XY-MOS MOSFET modules driven by an Arduino Nano ESP32 (Wi-Fi / Telemetrix).

    Axis "Fan"    → GPIO 17 (D8)  → MOSFET → 12 V fan
    Axis "Heater" → GPIO 18 (D9)  → MOSFET → resistive load / heater

    The actuator value is a PWM duty-cycle in the range **0-255**:
    - 0   → 0 % (fully off)
    - 255 → 100 % (fully on)
    """

    _controller_units = ""
    is_multiaxes = True

    # Map human-readable axis names to the corresponding GPIO pin numbers.
    # axis_value (used in move_abs / get_actuator_value) will be the GPIO int.
    _axis_names = {
        "Fan": _FAN_PIN,
        "Heater": _HEATER_PIN,
    }

    _epsilon = 1          # minimum meaningful step (1 PWM count)
    data_actuator_type = DataActuatorType["DataActuator"]

    params = [
        {
            "title": "ESP32 IP address:",
            "name": "esp32_ip",
            "type": "str",
            "value": _DEFAULT_IP,
        },
        {
            "title": "ESP32 TCP port:",
            "name": "esp32_port",
            "type": "int",
            "value": _DEFAULT_PORT,
        },
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def ini_attributes(self):
        self.controller: Optional[ESP32] = None

    def ini_stage(self, controller=None):
        """
        Initialise the connection to the ESP32.

        In the multi-axes / master-slave pattern PyMoDAQ creates one plugin
        instance per axis but only the *master* actually opens the hardware
        connection; slaves re-use the same controller object.
        """
        self.controller = self.ini_stage_init(
            old_controller=controller,
            new_controller=None,
        )

        if self.is_master:
            ip = self.settings["esp32_ip"]
            port = self.settings["esp32_port"]
            self.controller = ESP32(ip_address=ip, ip_port=port)
            self._configure_pins()

        info = (
            f"ESP32 Fan controller initialised — "
            f"IP={self.settings['esp32_ip']}:{self.settings['esp32_port']}"
        )
        initialized = True
        return info, initialized

    def _configure_pins(self):
        """Set every axis pin to PWM (analog output) mode."""
        for axis_name, pin in self._axis_names.items():
            self.controller.set_pin_mode_analog_output(
                pin,
                channel=_PIN_CHANNEL[pin],
                frequency=5000.0,   # 5 kHz – inaudible, good for MOSFETs
                resolution=8,       # 8-bit → 0-255
            )

    def close(self):
        """Turn off all outputs and close the connection."""
        if self.is_master:
            self.controller.set_pins_output_to(0)
            self.controller.shutdown()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def commit_settings(self, param: Parameter):
        """React to changes in the settings panel (none require live updates here)."""
        pass

    # ------------------------------------------------------------------
    # Actuator interface
    # ------------------------------------------------------------------

    def get_actuator_value(self) -> DataActuator:
        """
        Return the last PWM value sent to the current axis pin.

        Because the XY-MOS modules have no feedback, we return the memorised
        value (what was last written).
        """
        pin = self.axis_value   # axis_value holds the GPIO pin number
        raw = self.controller.get_output_pin_value(pin)
        pos = DataActuator(data=float(raw))
        pos = self.get_position_with_scaling(pos)
        return pos

    def move_abs(self, value: DataActuator):
        """
        Set the PWM duty cycle to an absolute value.

        Parameters
        ----------
        value:
            Target PWM duty cycle in [0, 255].
        """
        value = self.check_bound(value)
        self.target_value = value
        value = self.set_position_with_scaling(value)

        pin = self.axis_value
        channel = _PIN_CHANNEL[pin]
        self.controller.analog_write_and_memorize(pin, int(value.value()), channel=channel)
        self.emit_status(ThreadCommand("Update_Status", [f"Pin {pin} -> {int(value.value())}"]))

    def move_rel(self, value: DataActuator):
        """
        Change the PWM duty cycle by a relative amount.

        Parameters
        ----------
        value:
            Relative change (positive = increase, negative = decrease).
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        pin = self.axis_value
        channel = _PIN_CHANNEL[pin]
        self.controller.analog_write_and_memorize(pin, int(self.target_value.value()), channel=channel)

    def move_home(self):
        """Set the current axis to 0 (fan / heater off)."""
        pin = self.axis_value
        channel = _PIN_CHANNEL[pin]
        self.controller.analog_write_and_memorize(pin, 0, channel=channel)

    def stop_motion(self):
        """Immediately stop the current axis (set PWM to 0)."""
        pin = self.axis_value
        channel = _PIN_CHANNEL[pin]
        self.controller.analog_write_and_memorize(pin, 0, channel=channel)


if __name__ == "__main__":
    main(__file__)
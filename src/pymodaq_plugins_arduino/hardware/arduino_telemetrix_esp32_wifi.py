import numbers
from typing import Optional
from threading import Lock
import asyncio

from telemetrix_aio_esp32 import telemetrix_aio_esp32

lock = Lock()


class ArduinoWiFi(telemetrix_aio_esp32.TelemetrixAioEsp32):
    """Arduino Nano ESP32 WiFi connection wrapper.

    Child class of TelemetrixAioEsp32. Provides a synchronous interface
    compatible with PyMoDAQ plugins, mirroring the Arduino API.

    Attributes
    ----------
    ip_address : str
    pin_values_output : dict
    analog_pin_values_input : dict
    """

    COM_PORTS = []  # No serial port for WiFi — kept for UI compatibility

    def __init__(self, ip_address: Optional[str] = None, ip_port: int = 31336, *args, **kwargs):
        telemetrix_aio_esp32.TelemetrixAioEsp32.__init__(
            self, transport_address=ip_address, ip_port=ip_port,
            autostart=False, *args, **kwargs)
        self.pin_values_output = {}
        self.analog_pin_values_input = {0: 0,
                                        1: 0,
                                        2: 0,
                                        3: 0,
                                        4: 0,
                                        5: 0}  # Initialized dictionary for 6 analog channels


    def _run(self, coro):
        """Run a coroutine from a synchronous context."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


    @staticmethod
    def round_value(value):
        return max(0, min(255, int(value)))

    def set_pin_mode_analog_output(self, pin: int):
        """Configure a pin as PWM analog output."""
        self._run(super().set_pin_mode_analog_output(pin))

    def set_pins_output_to(self, value: int):
        lock.acquire()
        for pin in self.pin_values_output:
            self._run(self.analog_write(pin, int(value)))
        lock.release()

    def analog_write_and_memorize(self, pin: int, value: int):
        lock.acquire()
        value = self.round_value(value)
        self._run(self.analog_write(pin, value))
        self.pin_values_output[pin] = value
        lock.release()

    def get_output_pin_value(self, pin: int) -> numbers.Number:
        value = self.pin_values_output.get(pin, 0)
        return value


    def read_analog_pin(self, data):
        """
        Used as a callback function to read the value of the analog inputs.
        Data[0]: pin_type (not used here)
        Data[1]: pin_number: i.e. 0 is A0 etc.
        Data[2]: pin_value: an integer between 0 and 1023
        Data[3]: raw_time_stamp (not used here)
        :param data: a list in which are loaded the acquisition parameter analog input
        :return: a dictionary with the following structure {pin_number(int):pin_value(int)}
        """
        self.analog_pin_values_input[data[1]] = data[2]

    def set_analog_input(self, pin: int):
        """
        Activate the analog pin, make an acquisition, write in the callback, stop the analog reporting.
        :param pin: pin number, 1 is A1 etc.
        :return: acquisition parameters in the declared callback
        """
        lock.acquire()
        self._run(self.set_pin_mode_analog_input(pin, differential=0, callback=self.read_analog_pin))
        lock.release()


    async def shutdown(self):
        """Terminate the WiFi connection."""
        await super().shutdown()


if __name__ == '__main__':
    async def test():
        tele = ArduinoWiFi(ip_address='172.17.50.236', ip_port=31336)
        await tele.start_aio()
        print("Connexion OK !")
        await tele.shutdown()

    asyncio.run(test())
import asyncio
import threading
from threading import Lock
from telemetrix_aio_esp32 import telemetrix_aio_esp32

lock = Lock()

PIN_TO_CHANNEL = {
    17: 0,
    18: 1,
}

class ArduinoWifi:
    def __init__(self, ip_address):
        self.pin_values_output = {}
        self.analog_pin_values_input = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    async def _init_board(self, ip_address):
        self._board = telemetrix_aio_esp32.TelemetrixAioEsp32(
            transport_address=ip_address,
            autostart=False,
            loop=self._loop
        )
        await self._board.start_aio()

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=5)

    @staticmethod
    def round_value(value):
        return max(0, min(255, int(value)))

    def set_pin_mode_analog_output(self, pin):
        channel = PIN_TO_CHANNEL.get(pin, 0)
        self._run(self._board.set_pin_mode_analog_output(pin_number=pin, channel=channel))

    def analog_write(self, pin, value):
        self._run(self._board.analog_write(channel=pin, value=value))
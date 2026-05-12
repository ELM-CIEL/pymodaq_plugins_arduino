import asyncio
import threading
from threading import Lock
from telemetrix_aio_esp32 import telemetrix_aio_esp32

lock = Lock()

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
            autostart=True,
            loop=self._loop
        )
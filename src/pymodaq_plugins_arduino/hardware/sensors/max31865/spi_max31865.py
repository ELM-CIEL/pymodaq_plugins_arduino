import asyncio
from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi
from pymodaq_plugins_arduino.utils import Config

config = Config()

# Registres MAX31865
MAX31865_CONFIG_REG      = 0x00
MAX31865_CONFIG_BIAS     = 0x80
MAX31865_CONFIG_MODEAUTO = 0x40
MAX31865_RTDMSB_REG      = 0x01

# Constantes PT100
RTD_NOMINAL   = 100.0
RTD_REFERENCE = 430.0
RTD_A = 3.9083e-3
RTD_B = -5.775e-7


class MAX31865:
    """Driver pour le capteur PT100 via MAX31865 SPI.
    Les broches SPI sont lues depuis config_template.toml ou passées en paramètres.
    """

    def __init__(self, controller: ArduinoWifi,
                 cs_pin=None, sck_pin=None, miso_pin=None, mosi_pin=None):
        self._board = controller._board
        self._run = controller._run
        self.cs_pin   = cs_pin   or config('max31865', 'cs_pin')
        self.sck_pin  = sck_pin  or config('max31865', 'sck_pin')
        self.miso_pin = miso_pin or config('max31865', 'miso_pin')
        self.mosi_pin = mosi_pin or config('max31865', 'mosi_pin')

    def ini_max31865(self):
        # D'abord init SPI via Telemetrix (pour qu'il soit "activé")
        self._run(self._board.set_pin_mode_spi([self.cs_pin]))

        # Puis config MAX31865
        config_byte = MAX31865_CONFIG_BIAS | MAX31865_CONFIG_MODEAUTO
        self._run(self._board.spi_cs_control(self.cs_pin, 0))
        self._run(self._board.spi_write_blocking([MAX31865_CONFIG_REG | 0x80, config_byte]))
        self._run(self._board.spi_cs_control(self.cs_pin, 1))

    def read_rtd_resistance(self) -> float:
        data = []
        event = asyncio.Event()

        async def spi_callback(report):
            data.extend(report[3:])
            event.set()

        async def read():
            await self._board.spi_cs_control(self.cs_pin, 0)
            await self._board.spi_read_blocking(
                MAX31865_RTDMSB_REG,
                2,
                call_back=spi_callback
            )
            await asyncio.wait_for(event.wait(), timeout=5)
            await self._board.spi_cs_control(self.cs_pin, 1)

        self._run(read())

        msb = data[0]
        lsb = data[1]
        rtd_raw = ((msb << 8) | lsb) >> 1
        resistance = (rtd_raw / 32768.0) * RTD_REFERENCE
        return resistance

    def resistance_to_temperature(self, resistance: float) -> float:
        z1 = -RTD_A
        z2 = RTD_A ** 2 - (4 * RTD_B)
        z3 = (4 * RTD_B) / RTD_NOMINAL
        z4 = 2 * RTD_B
        temp = z2 + (z3 * resistance)
        temp = (temp ** 0.5 + z1) / z4
        return temp

    def get_temperature(self) -> float:
        resistance = self.read_rtd_resistance()
        return self.resistance_to_temperature(resistance)
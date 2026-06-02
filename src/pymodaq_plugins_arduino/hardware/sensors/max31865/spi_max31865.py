from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi

# Lecture des broches via fichier conf
CS_PIN  = config('max31865', 'cs_pin')
SCK_PIN = config('max31865', 'sck_pin')
MISO_PIN = config('max31865', 'miso_pin')
MOSI_PIN = config('max31865', 'mosi_pin')


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

    Les broches SPI sont lues depuis config_template.toml
    """

    def __init__(self, controller: ArduinoWifi):
        self._board = controller._board
        self._run = controller._run

    def ini_max31865(self):
        """Initialise le bus SPI avec les broches du fichier de config et
        configure le MAX31865 en mode automatique."""

        # Initialisation SPI avec les broches configurables
        # Le firmware reçoit : [sck, miso, mosi, nb_cs, cs_pin1, ...]
        self._run(self._board.set_pin_mode_spi(
            CS,
            sck=SCK_PIN,
            miso=MISO_PIN,
            mosi=MOSI_PIN
        ))

        # Configuration : bias ON + mode auto conversion
        config_byte = MAX31865_CONFIG_BIAS | MAX31865_CONFIG_MODEAUTO
        self._run(self._board.spi_cs_control(CS_PIN, 0))
        self._run(self._board.spi_write_blocking([MAX31865_CONFIG_REG | 0x80, config_byte]))
        self._run(self._board.spi_cs_control(CS_PIN, 1))

    def read_rtd_resistance(self) -> float:
        """Lit les registres RTD du MAX31865 et retourne la résistance en ohms."""
        import asyncio
        data = []
        event = asyncio.Event()

        async def spi_callback(report):
            data.extend(report[3:])
            event.set()

        async def read():
            await self._board.spi_cs_control(CS_PIN, 0)
            await self._board.spi_read_blocking(
                MAX31865_RTDMSB_REG,
                2,
                call_back=spi_callback
            )
            # On attend la réponse AVANT de relâcher le CS
            await asyncio.wait_for(event.wait(), timeout=5)
            await self._board.spi_cs_control(CS_PIN, 1)

        self._run(read())

        msb = data[0]
        lsb = data[1]
        rtd_raw = ((msb << 8) | lsb) >> 1
        resistance = (rtd_raw / 32768.0) * RTD_REFERENCE
        return resistance

    def resistance_to_temperature(self, resistance: float) -> float:
        """Convertit la résistance PT100 en température (°C)
        via l'équation de Callendar-Van Dusen."""
        z1 = -RTD_A
        z2 = RTD_A ** 2 - (4 * RTD_B)
        z3 = (4 * RTD_B) / RTD_NOMINAL
        z4 = 2 * RTD_B

        temp = z2 + (z3 * resistance)
        temp = (temp ** 0.5 + z1) / z4
        return temp

    def get_temperature(self) -> float:
        """Retourne directement la température en °C."""
        resistance = self.read_rtd_resistance()
        return self.resistance_to_temperature(resistance)

from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi

# Broches SPI Nano ESP32 (By GPIO number)
CS_PIN = 21
CS = [21]

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

    Broches SPI Nano ESP32 :
        SCK  → D13 = GPIO48
        MISO → D12 = GPIO47
        MOSI → D11 = GPIO38
        CS   → D10 = GPIO21
    """

    def __init__(self, controller: ArduinoWifi):
        self._board = controller._board
        self._run = controller._run

    def ini_max31865(self):
        """Initialise le bus SPI et configure le MAX31865 en mode automatique."""
        self._run(self._board.set_pin_mode_spi(CS))

        # Configuration : bias ON + mode auto conversion
        config = MAX31865_CONFIG_BIAS | MAX31865_CONFIG_MODEAUTO
        self._run(self._board.spi_cs_control(CS_PIN, 0))
        self._run(self._board.spi_write_blocking([MAX31865_CONFIG_REG | 0x80, config]))
        self._run(self._board.spi_cs_control(CS_PIN, 1))

    def read_rtd_resistance(self) -> float:
        """Lit les registres RTD du MAX31865 et retourne la résistance en ohms."""
        data = []

        async def spi_callback(report):
            data.extend(report[3:])

        self._run(self._board.spi_cs_control(CS_PIN, 0))
        self._run(self._board.spi_read_blocking(
            MAX31865_RTDMSB_REG,
            2,
            call_back=spi_callback
        ))
        self._run(self._board.spi_cs_control(CS_PIN, 1))

        msb = data[0]
        lsb = data[1]
        rtd_raw = ((msb << 8) | lsb) >> 1  # retire le bit de fault
        resistance = (rtd_raw / 32768.0) * RTD_REFERENCE
        return resistance
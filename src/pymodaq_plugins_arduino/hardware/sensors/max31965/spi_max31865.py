from pymodaq_plugins_arduino.hardware.esp32_telemetrix import ArduinoWifi

# Broches SPI Nano ESP32 (By GPIO number)
CS_PIN = 21   # D10 = GPIO21
CS = [21]

# Registres MAX31865
MAX31865_CONFIG_REG      = 0x00
MAX31865_CONFIG_BIAS     = 0x80
MAX31865_CONFIG_MODEAUTO = 0x40
MAX31865_RTDMSB_REG      = 0x01

# Constantes PT100
RTD_NOMINAL   = 100.0   # résistance nominale PT100
RTD_REFERENCE = 430.0   # résistance de référence sur le module
RTD_A = 3.9083e-3
RTD_B = -5.775e-7


class MAX31865(ArduinoWifi):
    """Driver pour le capteur PT100 via MAX31865 SPI.

    Broches SPI Nano ESP32 :
        SCK  → D13 = GPIO48
        MISO → D12 = GPIO47
        MOSI → D11 = GPIO38
        CS   → D10 = GPIO21
    """
    pass
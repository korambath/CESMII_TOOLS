import board
import time
from adafruit_bme280 import basic as adafruit_bme280

# Two sensors RaspberryPI connection information
'''
    VCC pin from both sensors to either 3.3V. If you are using an Arduino Uno, use the 5V pin.
    GND pin from both sensors to the GND pin on your RaspberryPI/Arduino.
    SCK pin from both sensors to the I2C clock SCL pin on your RaspberryPI/Arduino. On the Arduino Uno that would be the pin A5.
    SDI pin from both sensors to the I2C data SDA pin on your RaspberryPI/Arduino. On the Arduino Uno that would be the pin A4.
    Leave the CS pin from both sensors unconnected.
    Leave the SDO pin from only one sensor unconnected.
    Connect the SDO pin from the other sensor to the GND on your RaspberryPI/Arduino

    sudo i2cdetect -y 1 on RaspberyPI should now show the address 76 and 77 (default)

'''

i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
bme280_2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

print("\nTemperature: %0.1f C" % bme280.temperature)
print("Humidity: %0.1f %%" % bme280.humidity)
print("Pressure: %0.1f hPa" % bme280.pressure)

bme280.sea_level_pressure = 1013.4
bme280_2.sea_level_pressure = 1013.4

print("Altitude = %0.2f meters" % bme280.altitude)

import math
b = 17.62
c = 243.12
gamma = (b * bme280.temperature /(c + bme280.temperature)) + math.log(bme280.humidity / 100.0)
dewpoint = (c * gamma) / (b - gamma)

print("Dewpoint: %0.1f C\n" %  dewpoint)

while True:
    print("\nFirst BME Sensor\n")
    print('{:05.2f} C {:05.2f} hPa {:05.2f} %'.format(bme280.temperature, bme280.pressure, bme280.humidity))
    print("\nSecond BME Sensor\n")
    print('{:05.2f} C {:05.2f} hPa {:05.2f} %'.format(bme280_2.temperature, bme280_2.pressure, bme280_2.humidity))
    time.sleep(5)



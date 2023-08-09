import board
import digitalio
import math
import time
import sys
from adafruit_bme280 import basic as adafruit_bme280
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
bme280 = adafruit_bme280.Adafruit_BME280_SPI(spi, cs)

# https://github.com/adafruit/Adafruit_CircuitPython_BME280/tree/main
# https://learn.adafruit.com/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout/python-circuitpython-test
# Wiring for SPI

#    Pi 3V3 to sensor VIN
#    Pi GND to sensor GND
#    Pi MOSI to sensor SDI
#    Pi MISO to sensor SDO
#    Pi SCLK to sensor SCK
#    Pi #5 to sensor CS (or use any other free GPIO pin) GPIO5 Pin # 29


bme280.sea_level_pressure = 1013.4

print("\nTemperature: %0.1f C" % bme280.temperature)
print("Humidity: %0.1f %%" % bme280.humidity)
print("Pressure: %0.1f hPa" % bme280.pressure)

print("Altitude = %0.2f meters" % bme280.altitude)



#b = 17.62
#c = 243.12
def computeDewpoint(temperature, humidity):
    b = 17.62
    c = 243.12
    gamma = (b * temperature /(c + temperature)) + math.log(humidity / 100.0)
    dewpoint = (c * gamma) / (b - gamma)
    #print(dewpoint)
    return dewpoint

def computeHeatIndex(temperature, humidity):
    # http://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml
    hi_coeff1 = -42.379
    hi_coeff2 =   2.04901523
    hi_coeff3 =  10.14333127
    hi_coeff4 =  -0.22475541
    hi_coeff5 =  -0.00683783
    hi_coeff6 =  -0.05481717
    hi_coeff7 =   0.00122874
    hi_coeff8 =   0.00085282
    hi_coeff9 =  -0.00000199
    temperature = (temperature * (9.0 / 5.0) + 32.0) # conversion to [°F]
    if temperature <= 40:
       heatIndex = temperature
    else:
       heatIndex = 0.5 * (temperature + 61.0 + ((temperature - 68.0) * 1.2) + (humidity * 0.094))	#calculate A -- from the official site,
       if heatIndex >= 79:
          heatIndex = hi_coeff1 + (hi_coeff2 + hi_coeff4 * humidity + temperature * (hi_coeff5 + hi_coeff7 * humidity)) * temperature \
                                + (hi_coeff3 + humidity * (hi_coeff6 + temperature * (hi_coeff8 + hi_coeff9 * temperature))) * humidity
          if ((humidity < 13) and (temperature >= 80.0) and (temperature <= 112.0)):
             heatIndex -= ((13.0 - humidity) * 0.25) * sqrt((17.0 - abs(temperature - 95.0)) * 0.05882)
          elif ((humidity > 85.0) and (temperature >= 80.0) and (temperature <= 87.0)):
             heatIndex += (0.02 * (humidity - 85.0) * (87.0 - temperature))
             
    return (heatIndex - 32.0) * (5.0 / 9.0) # convert to degree C

#print(computeHeatIndex(bme280.temperature, bme280.humidity))

while True:
    print("\nTemperature: %0.1f C" % bme280.temperature)
    print("Humidity: %0.1f %%" % bme280.relative_humidity)
    print("Pressure: %0.1f hPa" % bme280.pressure)
    print("Altitude = %0.2f meters" % bme280.altitude)
    print("Dewpoint = %0.1f C" % computeDewpoint(bme280.temperature, bme280.humidity))
    print("Heat Index = %0.1f C" % computeHeatIndex(bme280.temperature, bme280.humidity))
    time.sleep(2)

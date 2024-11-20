import asyncio
import logging
import random
import json
import time
from datetime import datetime
import serial

from asyncua import Server, ua

# Serial Port Configuration
#SERIAL_PORT = '/dev/cu.usbmodem2101'
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600  # Baud rate for the serial communication
SERIAL_TIMEOUT = 1  # Timeout for reading from serial port in seconds

# Configure logging
#logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.basicConfig(level=logging.WARN, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def main() -> None:
    # Setup OPC UA server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # Register namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # Create address space
    weather_obj = await server.nodes.objects.add_object(idx, "WeatherObject")
    temperature = await weather_obj.add_variable(idx, "Temperature", 16.7)
    pressure = await weather_obj.add_variable(idx, "Pressure", 900.0)
    humidity = await weather_obj.add_variable("ns=2;s=Sensor.Tags.humidity", "Humidity", 50.0)

    # Make variables writable
    await asyncio.gather(
        temperature.set_writable(),
        pressure.set_writable(),
        humidity.set_writable()
    )

    logger.info("OPC UA server started.")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT)
    except serial.SerialException as e:
        logger.error(f"Failed to open serial port: {e}")
        return

    async with server:
        while True:
            await asyncio.sleep(1)

            try:
                line = ser.readline().decode("utf-8").strip()  # Read until newline

                # Check if we received a line
                if not line:
                    logger.warning("Received empty line from serial port.")
                    continue

                line_split = line.split(",")  # Split the line into a list

                # Ensure the data is valid and contains the right number of values
                if len(line_split) != 4:
                    logger.error(f"Invalid data received: {line}")
                    continue

                # Parse float values from the list
                try:
                    temp, press, alt, hum = map(float, line_split)
                except ValueError as e:
                    logger.error(f"Error converting data to float: {e}")
                    continue

                # Update the OPC UA variables
                await asyncio.gather(
                    temperature.write_value(temp),
                    pressure.write_value(press),
                    humidity.write_value(hum)
                )

                print(f"Updated values - Temperature: {temp} Pressure: {press} Humidity: {hum}")

                logger.info("Updated values - Temperature: %.2f, Pressure: %.2f, Humidity: %.2f",
                            temp, press, hum)

            except serial.SerialException as e:
                logger.error(f"Serial communication error: {e}")
                break
            except Exception as e:
                logger.exception(f"Unexpected error: {e}")
                continue

if __name__ == "__main__":
    #logging.basicConfig(level=logging.WARN)
    asyncio.run(main())


import asyncio
import logging
import random

from asyncua import Server, ua

# Constants for variable limits
TEMP_RANGE = (0, 100)
PRESSURE_RANGE = (900, 1000)
HUMIDITY_RANGE = (0, 100)

async def update_variable(variable, lo: float, hi: float, logger: logging.Logger) -> None:
    """Update the variable with a random value within the specified range."""
    new_val = round(random.uniform(lo, hi), 2)
    await variable.write_value(new_val)
    logger.info("Updated %s to %.2f", variable, new_val)

async def main() -> None:
    logger = logging.getLogger(__name__)

    # Setup OPC UA server
    server = Server()
    await server.init()
    #server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_endpoint("opc.tcp://192.168.1.3:4840/freeopcua/server/")

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

    logger.info("Starting server!")

    async with server:
        while True:
            await asyncio.sleep(1)
            await asyncio.gather(
                update_variable(temperature, *TEMP_RANGE, logger),
                update_variable(pressure, *PRESSURE_RANGE, logger),
                update_variable(humidity, *HUMIDITY_RANGE, logger)
            )

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    asyncio.run(main(), debug=True)


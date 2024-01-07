import asyncio
import logging
import random

from asyncua import Server, ua
from asyncua.common.methods import uamethod


@uamethod
def func(parent, value):
    return value * 2

@uamethod
def multiply(parent, x, y):
    print("\nmultiply method call with parameters: ", x, y)
    print("\n")
    return x * y

async def update_variable(MyVar, lo, hi, _logger):
    new_val = round (random.uniform(lo, hi), 2)
    await MyVar.write_value(new_val)
    _logger.info("Set value of %s to %.2f ", await MyVar.read_browse_name(), new_val)
    


async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # set up our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    weatherobj = await server.nodes.objects.add_object(idx, "WeatherObject")
    temperature = await weatherobj.add_variable(idx, "Temperature", 16.7)
    pressure = await weatherobj.add_variable(idx, "Pressure", 900.0)
    # Set Variables to be writable by clients
    await temperature.set_writable()
    await pressure.set_writable()
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        func,
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethodMult", idx),
        ua.QualifiedName("ServerMethodMult", idx),
        multiply,
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            await update_variable(temperature, 0, 100,  _logger)
            await update_variable(pressure, 900, 1000, _logger)


if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.WARN)
    #logging.basicConfig(level=logging.INFO)
    asyncio.run(main(), debug=True)

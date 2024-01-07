import asyncio
import logging
import time
import json
import sys

from asyncua import Client

url = "opc.tcp://localhost:4840/freeopcua/server/"
namespace = "http://examples.freeopcua.github.io"


async def main():

    _logger = logging.getLogger(__name__)
    print(f"Connecting to {url} ...")
    async with Client(url=url) as client:
        # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
        root = client.get_root_node()
        root = client.nodes.root
        _logger.info("Objects node is: %s", root)
        print(f'Object node is  "{root}" .')


        # Find the namespace index
        nsidx = await client.get_namespace_index(namespace)
        print(f"Namespace Index for '{namespace}': {nsidx}")

        # Get the variable node for read / write
        varT = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:WeatherObject", f"{nsidx}:Temperature"]
        )
        value = await varT.read_value()
        print(f"Value of MyVariable ({varT}): {value}")


        varP = await client.nodes.root.get_child(
            ["0:Objects", f"{nsidx}:WeatherObject", f"{nsidx}:Pressure"]
        )
        value = await varP.read_value()
        print(f"Value of MyVariable ({varP}): {value}")
        # Calling a method
        res = await client.nodes.objects.call_method(f"{nsidx}:ServerMethod", 5)
        print(f"Calling ServerMethod returned {res}")

        res = await client.nodes.objects.call_method(f"{nsidx}:ServerMethodMult", 5, 3)
        print(f"Calling ServerMethodMult returned {res}")
        sensorNode = [varT, varP]


        while True:
             value = []
             for sensor in sensorNode:
                  var = await sensor.read_value()
                  value.append(var)

             message = {
              "timestamp": time.time(),
              "opc_temperature": value[0],
              "opc_pressure": value[1]
             }
             json_data = json.dumps(message)
             #print(message)
             print(json_data)
             time.sleep(1)
       
        try:
             await client.disconnect()
        except Exception as e:  # catching all exceptions is not always wise!
             print(e)
             return


if __name__ == "__main__":
    asyncio.run(main())

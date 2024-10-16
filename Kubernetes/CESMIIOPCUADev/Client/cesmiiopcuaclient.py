import argparse
import asyncio
import logging
import json
import time
from asyncua import Client, ua, Node

async def browse_children(objects: Node) -> tuple[list[str], list[float]]:
    """Browse child nodes and return their browse names and values."""
    children = await objects.get_children()
    var_list, val_list = [], []

    for child in children:
        browse_name = await child.read_browse_name()
        value = await child.read_value()
        var_list.append(browse_name.Name)
        val_list.append(value)
        
    return var_list, val_list

async def main(url: str) -> None:
    logger = logging.getLogger(__name__)
    logger.info("Connecting to %s ...", url)

    async with Client(url=url) as client:
        root = client.get_root_node()
        logger.info("Objects node is: %s", root)
        namespace = "http://examples.freeopcua.github.io"
        objectname="WeatherObject"
        print(f'Namespace is: {namespace} url is: {url} Object name is: {objectname}.')

        idx = await client.get_namespace_index(namespace)
        weather_obj = await client.get_objects_node().get_child([f'{idx}:{objectname}'])
        logger.info("{objectname} Node is: %s", weather_obj)
        print(f'Object {objectname} Node is: "{weather_obj}" and index is {idx}.')

        while True:
            var_list, val_list = await browse_children(weather_obj)
            message = {
                "timestamp": time.time(),
            }
            message.update(dict(zip(var_list, val_list)))

            json_data = json.dumps(message, indent=3)
            print(json_data)

            await asyncio.sleep(1)  # Use asyncio.sleep instead of time.sleep

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OPC UA Client")
    parser.add_argument('url', type=str, help='OPC UA Server URL')
    args = parser.parse_args()

    #logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.CRITICAL)
    try:
        asyncio.run(main(args.url))
    except Exception as e:
        print(f"An error occurred: {e}")


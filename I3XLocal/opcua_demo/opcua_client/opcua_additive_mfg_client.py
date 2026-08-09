#!/usr/bin/env python3

import argparse
import asyncio
import json
import os

from asyncua import Client


SERVER_URL = os.getenv(
    "OPCUA_SERVER_URL",
    "opc.tcp://127.0.0.1:4840/freeopcua/server/",
)

AM_NAMESPACE = (
    "http://opcfoundation.org/UA/AdditiveManufacturing/"
)

MACHINE_OBJECT = "AdditiveManufacturingMachine"


async def read_engineering_units(node):
    """Read the EngineeringUnits property from a variable node if present."""
    try:
        properties = await node.get_children()
    except Exception:
        return None

    for prop in properties:
        try:
            browse_name = await prop.read_browse_name()
        except Exception:
            continue

        if browse_name.Name == "EngineeringUnits":
            try:
                eu = await prop.read_value()
            except Exception:
                return None

            display_name = getattr(getattr(eu, "DisplayName", None), "Text", None)
            if display_name:
                return display_name

            return getattr(eu, "UnitId", None)

    return None


class SubscriptionHandler:
    """
    Handles OPC UA data change notifications.
    """

    def __init__(self, namespace_array):
        self.namespace_array = namespace_array


    async def datachange_notification(
        self,
        node,
        value,
        data,
    ):

        dv = data.monitored_item.Value

        browse_name = await node.read_browse_name()
        display_name = await node.read_display_name()

        nodeid = node.nodeid

        namespace_uri = None
        if 0 <= nodeid.NamespaceIndex < len(self.namespace_array):
            namespace_uri = self.namespace_array[nodeid.NamespaceIndex]

        unit = await read_engineering_units(node)

        message = {
            "browse_name": browse_name.Name,
            "display_name": display_name.Text,
            "namespace": namespace_uri,
            "node_id": nodeid.to_string(),
            "value": value,
            "unit": unit,
            "source_timestamp": (
                dv.SourceTimestamp.isoformat()
                if dv.SourceTimestamp
                else None
            ),
            "server_timestamp": (
                dv.ServerTimestamp.isoformat()
                if dv.ServerTimestamp
                else None
            ),
            "status": str(dv.StatusCode),
        }

        print(
            json.dumps(
                message,
                indent=2,
                default=str,
                ensure_ascii=False,
            )
        )


    async def event_notification(self, event):
        print("Event:", event)



async def subscribe_recursive(
    node,
    subscription,
):

    node_class = await node.read_node_class()

    if node_class.name == "Variable":

        browse_name = await node.read_browse_name()

        print(
            f"Subscribing: {browse_name.Name}"
        )

        await subscription.subscribe_data_change(
            node
        )

        return


    children = await node.get_children()

    for child in children:
        await subscribe_recursive(
            child,
            subscription,
        )



async def main(args=None):
    parser = argparse.ArgumentParser(description="Subscribe to the OPC UA additive manufacturing demo server")
    parser.add_argument("--server-url", default=os.getenv("OPCUA_SERVER_URL", SERVER_URL))
    parsed_args = parser.parse_args(args)

    server_url = parsed_args.server_url

    async with Client(
        url=server_url
    ) as client:

        print(
            f"Connected to {server_url}"
        )


        namespace_array = (
            await client.get_namespace_array()
        )

        print("\nNamespaces:")
        for idx, uri in enumerate(namespace_array):
            print(
                f"{idx}: {uri}"
            )


        #
        # Find AM namespace dynamically
        #

        am_idx = (
            await client.get_namespace_index(
                AM_NAMESPACE
            )
        )


        print(
            f"\nAM Namespace index = {am_idx}"
        )


        #
        # Navigate address space
        #

        objects = client.nodes.objects

        am_machine = await objects.get_child(
            [
                f"{am_idx}:{MACHINE_OBJECT}"
            ]
        )


        print(
            "Found:",
            await am_machine.read_browse_name()
        )


        #
        # Create subscription
        #

        handler = SubscriptionHandler(
            namespace_array
        )

        subscription = await client.create_subscription(
            1000,
            handler,
        )


        #
        # Subscribe to all machine variables
        #

        await subscribe_recursive(
            am_machine,
            subscription,
        )


        print(
            "\nWaiting for AM telemetry..."
        )


        try:
            while True:
                await asyncio.sleep(60)

        finally:
            await subscription.delete()



if __name__ == "__main__":

    asyncio.run(main())

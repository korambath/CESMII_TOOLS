#!/usr/bin/env python3
"""Live plot of AM machine telemetry using asyncua + matplotlib."""

import asyncio
import collections
import threading

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from asyncua import Client

SERVER_URL = "opc.tcp://127.0.0.1:4840/freeopcua/server/"
AM_NS = "http://opcfoundation.org/UA/AdditiveManufacturing/"
HISTORY = 120  # number of data points to keep per variable

# Shared buffer — written by the asyncio thread, read by the plot thread
buffers: dict[str, collections.deque] = {
    "ChamberTemperature": collections.deque(maxlen=HISTORY),
    "SubstrateTemperature": collections.deque(maxlen=HISTORY),
    "LaserPowerOutput": collections.deque(maxlen=HISTORY),
    "PowderLevelPercentage": collections.deque(maxlen=HISTORY),
}


class PlotHandler:
    async def datachange_notification(self, node, value, data):
        name = (await node.read_browse_name()).Name
        if name in buffers and isinstance(value, (int, float)):
            buffers[name].append(value)

    async def event_notification(self, event):
        pass


async def opcua_loop():
    async with Client(url=SERVER_URL) as client:
        am_idx = await client.get_namespace_index(AM_NS)
        machine = await client.nodes.objects.get_child(
            [f"{am_idx}:AdditiveManufacturingMachine"]
        )
        process_values = await machine.get_child(
            [f"{am_idx}:ProcessValues"]
        )

        handler = PlotHandler()
        sub = await client.create_subscription(500, handler)

        nodes = []
        for name in buffers:
            node = await process_values.get_child([f"{am_idx}:{name}"])
            nodes.append(node)

        await sub.subscribe_data_change(nodes)
        print("Subscribed. Close the plot window to exit.")

        # Keep running until the plot window is closed
        while plt.get_fignums():
            await asyncio.sleep(0.2)

        await sub.delete()


def start_asyncio():
    asyncio.run(opcua_loop())


def main():
    fig, axes = plt.subplots(2, 2, figsize=(12, 7))
    fig.suptitle("AM Machine — Live Telemetry")

    plots = {
        name: ax
        for name, ax in zip(buffers.keys(), axes.flat)
    }
    lines = {}
    for name, ax in plots.items():
        (line,) = ax.plot([], [], lw=1.5)
        ax.set_title(name)
        ax.set_xlabel("Sample")
        lines[name] = line

    def update(_frame):
        for name, line in lines.items():
            data = list(buffers[name])
            if data:
                line.set_data(range(len(data)), data)
                plots[name].relim()
                plots[name].autoscale_view()
        return lines.values()

    # Run the OPC UA client in a background thread
    t = threading.Thread(target=start_asyncio, daemon=True)
    t.start()

    _anim = animation.FuncAnimation(fig, update, interval=500, blit=False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

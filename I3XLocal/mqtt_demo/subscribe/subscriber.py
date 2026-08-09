import json

import paho.mqtt.client as mqtt

#BROKER = "192.168.1.100"       # Change to your MQTT broker IP
BROKER = "127.0.0.1"       # Change to your MQTT broker IP
PORT = 1883
TOPIC = "cesmii/labLA/bme280sensor"


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}\n")


def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    print("Received:")
    print(json.dumps(payload, indent=4))
    print("=" * 50)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

print("Subscriber waiting for data...\n")

client.loop_forever()

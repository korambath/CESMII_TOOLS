import json
import random
import time
from datetime import datetime

import paho.mqtt.client as mqtt

#BROKER = "192.168.1.100"       # Change to your MQTT broker IP
BROKER = "127.0.0.1"       # Change to your MQTT broker IP
PORT = 1883
TOPIC = "cesmii/labLA/bme280sensor"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)

print("Publisher started...\n")

try:
    while True:
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "temperature": round(random.uniform(20.0, 35.0), 2),
            "humidity": round(random.uniform(30.0, 80.0), 2),
            "pressure": round(random.uniform(990.0, 1035.0), 2)
        }

        client.publish(TOPIC, json.dumps(payload))

        print("Published:")
        print(json.dumps(payload, indent=4))
        print("-" * 50)

        time.sleep(2)

except KeyboardInterrupt:
    print("\nPublisher stopped.")

client.disconnect()

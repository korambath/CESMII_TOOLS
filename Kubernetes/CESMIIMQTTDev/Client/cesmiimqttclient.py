import paho.mqtt.client as mqtt
import json
from datetime import datetime, timezone
import sys

# Define the MQTT settings
#MQTT_BROKER = "your_mqtt_broker_url"  # Replace with your MQTT broker URL
#MQTT_BROKER = "0.0.0.0"  # Replace with your MQTT broker URL
#MQTT_BROKER = "192.168.1.14"  # Replace with your MQTT broker URL
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = "Envsensor/data"  # Replace with your topic

# Initialize a message counter
msg_count = 0

def on_connect(client, userdata, flags, rc):
    if rc == 0:
       print(f"Connected to MQTT Broker !")
       print(f"Connected with result code {rc}")
    else:
       print(f"Failed to connect, return code {rc}\n")

    print(f"Subscribing to topic {MQTT_TOPIC}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global msg_count
    msg_count += 1  # Increment the message counter
    try:
        data = json.loads(msg.payload.decode())
        temperature = data.get("temperature")
        humidity = data.get("humidity")
        pressure = data.get("pressure")
        now = datetime.now()
        print(f"Message {msg_count} received {msg.topic} :  temperature: {temperature}°C, humidity: {humidity}%, pressure: {pressure} mbar at {now} ")
    except json.JSONDecodeError:
        print("Received non-JSON message")

def main(mqtt_broker):
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"connecting to broker {mqtt_broker} at port {MQTT_PORT} \n")
    # Connect to the MQTT broker
    try:
        client.connect(mqtt_broker, MQTT_PORT, 60)
    except Exception as e:
        print(f"Could not connect to MQTT broker {mqtt_broker}: {e}")
        return
    #client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python cesmiimqttclient.py <mqtt_broker>")
        sys.exit(1)
    mqtt_broker = sys.argv[1]
    main(mqtt_broker)


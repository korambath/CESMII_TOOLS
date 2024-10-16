import paho.mqtt.client as mqtt
import random
import time
import json
from datetime import datetime, timezone

# Define the MQTT settings
MQTT_BROKER = "192.168.1.14"  # Listen on all interfaces
MQTT_PORT = 1883
MQTT_TOPIC = "Envsensor/data"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker! \n")
        print(f"Connected with result code {rc} \n")
    else:
        print(f"Failed to connect, return code {rc}\n")

def on_log(client, userdata, level, buffer):
     print("Log ", buffer)



def publish_data(client):
    msg_count = 0
    while True:
        # Generate random temperature and humidity data
        temperature = round(random.uniform(20.0, 30.0), 2)  # Random temperature between 20 and 30
        humidity = round(random.uniform(30.0, 70.0), 2)      # Random humidity between 30% and 70%
        pressure = round(random.uniform(990.0, 1040.0), 2)    # Random pressure between 900 and 1050 mbar
        
        # Create the payload
        payload = json.dumps({
            "temperature": temperature,
            "humidity": humidity,
            "pressure": pressure
        })
        
        now = datetime.now()
        # Publish the message
        result = client.publish(MQTT_TOPIC, payload)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Published {msg_count} : {payload} to topic {MQTT_TOPIC} at {now}")
        else:
            print(f"Failed to send message to topic {topic}")

        
        # Wait for 5 seconds before sending the next message
        time.sleep(2)
        msg_count += 1

def main():
    client = mqtt.Client()
    client.on_connect = on_connect

    print(f"connecting to broker {MQTT_BROKER} at port {MQTT_PORT} \n")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    #client.on_log = on_log # Debug

    client.loop_start()  # Start the loop

    print(f"Publishing to topic {MQTT_TOPIC} \n")
    publish_data(client)  # Start publishing data

    client.loop_stop()  # Stop the loop

if __name__ == "__main__":
    main()


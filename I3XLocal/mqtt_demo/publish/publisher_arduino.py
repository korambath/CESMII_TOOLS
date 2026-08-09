import json
import time
import serial
from datetime import datetime

import paho.mqtt.client as mqtt

# MQTT settings
BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "cesmii/labLA/bme280sensor"

# Arduino serial settings

# Arduino serial settings
SERIAL_PORT = "/dev/cu.usbmodem2101"
BAUD_RATE = 9600

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT, 60)

print("Publisher started...\n")

# Open Arduino serial connection
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)  # Allow Arduino time to reset
    print(f"Connected to Arduino on {SERIAL_PORT}")

except serial.SerialException as e:
    print(f"Failed to open serial port: {e}")
    exit()


try:
    while True:
        # Read Arduino data
        line = ser.readline().decode("utf-8").strip()

        if not line:
            continue

        try:
            # Arduino sends:
            # temperature,pressure,altitude,humidity
            temperature, pressure, altitude, humidity = map(float, line.split(","))
            #    "altitude": round(altitude, 2)

            payload = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "temperature": round(temperature, 2),
                "humidity": round(humidity, 2),
                "pressure": round(pressure, 2),
            }

            client.publish(TOPIC, json.dumps(payload))

            print("Published:")
            print(json.dumps(payload, indent=4))
            print("-" * 50)

        except ValueError:
            print(f"Invalid Arduino data: {line}")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nPublisher stopped.")

finally:
    ser.close()
    client.disconnect()


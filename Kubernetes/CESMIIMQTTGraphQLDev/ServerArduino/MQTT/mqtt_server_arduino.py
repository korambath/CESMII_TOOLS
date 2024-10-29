import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import serial

# MQTT Settings
#MQTT_BROKER = "127.0.0.1"  
MQTT_BROKER = "192.168.1.14"
MQTT_PORT = 1883
MQTT_TOPIC = "Envsensor/data"

# Serial Port Configuration
#SERIAL_PORT = '/dev/cu.usbmodem2101'
SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600  # Baud rate for the serial communication

def on_connect(client, userdata, flags, rc):
    """Callback when the client connects to the broker."""
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {rc}")

def publish_data(client):
    """Read data from the serial port and publish it to the MQTT topic."""
    msg_count = 0

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
        return

    while True:
        try:
            line = ser.readline().decode("utf-8").strip()  # Read until newline
            line_split = line.split(",")  # Split the line into a list

            # Parse float values from the list
            temperature, pressure, altitude, humidity = map(float, line_split)

            # Create the payload
            payload = json.dumps({
                "temperature": temperature,
                "humidity": humidity,
                "pressure": pressure
            })

            # Publish the message
            result = client.publish(MQTT_TOPIC, payload)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published {msg_count}: {payload} to topic {MQTT_TOPIC} at {datetime.now()}")
            else:
                print(f"Failed to send message to topic {MQTT_TOPIC}")

            msg_count += 1
            time.sleep(2)  # Wait for 3 seconds before sending the next message

        except (ValueError, IndexError) as e:
            print(f"Error processing data: {e}")
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            break

def main():
    """Main function to set up the MQTT client and start publishing data."""
    client = mqtt.Client()
    client.on_connect = on_connect

    print(f"Connecting to broker {MQTT_BROKER} at port {MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()  # Start the loop

    print(f"Publishing to topic {MQTT_TOPIC}...")
    publish_data(client)  # Start publishing data

    client.loop_stop()  # Stop the loop

if __name__ == "__main__":
    main()


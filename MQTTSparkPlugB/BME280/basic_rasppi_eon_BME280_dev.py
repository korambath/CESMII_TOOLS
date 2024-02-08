import time
import random

from mqtt_spb_wrapper import *

# If you are not using rasperryPI sensor BME280 set it in simulation mode to generate
# random data by seetting raspPI=False
# If you are on raspberryPI and have BME280 sensor set raspPI=True else raspPI=False

raspPI=False

if raspPI:
     import board
     from adafruit_bme280 import basic as adafruit_bme280

     # Create sensor object, using the board's default I2C bus.
     i2c = board.I2C()  # uses board.SCL and board.SDA
     bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)


     # change this to match the location's pressure (hPa) at sea level
     bme280.sea_level_pressure = 1013.4

_DEBUG = True  # Enable debug messages

print("--- Sparkplug B example - End of Node Device - Simple")

def callback_command(payload):
    print("DEVICE received CMD: %s" % (payload))


def callback_message(topic, payload):
    print("Received MESSAGE: %s - %s" % (topic, payload))


# Create the spB entity object
group_name = "Group-001"
edge_node_name = "RaspPI-001"
device_name = "BME280Sensor1"
device2_name = "BME280Sensor2"

# Namespace = spBv1.0
# GroupID
# MessageType
# Edge of Network Node ID
# DeviceID

 
# spBv1.0/[Group ID]/[Message Type]/[EON Node ID]/[Device ID]

device = MqttSpbEntityDevice(group_name, edge_node_name, device_name, _DEBUG)

device.on_message = callback_message  # Received messages
device.on_command = callback_command  # Callback for received commands



# Set the device Attributes, Data and Commands that will be sent on the DBIRTH message --------------------------

# Attributes
device.attribures.set_value("description", "Simple EoN Device RaspPI")
device.attribures.set_value("type", "BME280-EoND-device")
device.attribures.set_value("version", "0.01")
device.attribures.set_value("SerialNumber", "123457890")
device.attribures.set_value("DeviceID", "57890")


# Data / Telemetry
device.data.set_value("temperature", 0)
device.data.set_value("humidity", 0)

# Commands
device.commands.set_value("rebirth", True)

# Connect to the broker --------------------------------------------
_connected = False
while not _connected:
    print("Trying to connect to broker...")
    _connected = device.connect("localhost", 1883)
    if not _connected:
        print("  Error, could not connect. Trying again in a few seconds ...")
        time.sleep(3)

# Send birth message
device.publish_birth()


# Send some telemetry values ---------------------------------------
value = 0  # Simple counter
for i in range(10):
    # Update the data value

    if raspPI:
        temperature = bme280.temperature
        humidity = bme280.relative_humidity 
    else:
        temperature = random.randint(20, 50)
        humidity = random.randint(0, 100)

    device.data.set_value("temperature", temperature)
    device.data.set_value("humidity", humidity)


    # Send data values
    print("Sending data - value : temperature: %0.3f C   " % temperature)
    print("Sending data - value : humidity: %0.3f %% " %  humidity)
    device.publish_data()

    # Increase counter
    value += 1

    # Sleep some time
    time.sleep(5)

# Disconnect device -------------------------------------------------
# After disconnection the MQTT broker will send the entity DEATH message.
print("Disconnecting device")
device.disconnect()

print("Application finished !")


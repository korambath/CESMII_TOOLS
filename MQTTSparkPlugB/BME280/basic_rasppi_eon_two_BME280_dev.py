import time
import random

from mqtt_spb_wrapper import *

'''
  In this example we have two identical BME280 sensors connected to RaspberryPI
  on address 76 and address 77 (default).  This is just to demonstrate the ability
  to send data from multiple sensors
  The first sensor is called device, and the second is called device2.  You can 
  add more if you have.
  If you are on raspberryPI set raspPI=True else raspPI=False
'''

raspPI=False
if raspPI:
     import board
     from adafruit_bme280 import basic as adafruit_bme280

     # Create sensor object, using the board's default I2C bus.
     i2c = board.I2C()  # uses board.SCL and board.SDA
     bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
     bme280_2 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)


     # change this to match the location's pressure (hPa) at sea level
     bme280.sea_level_pressure = 1013.4
     bme280_2.sea_level_pressure = 1013.4



_DEBUG = True  # Enable debug messages

print("--- Sparkplug B example - End of Node Device - Simple")


def callback_command(payload):
    print("DEVICE received CMD: %s" % (payload))


def callback_message(topic, payload):
    print("Received MESSAGE: %s - %s" % (topic, payload))



# Namespace = spBv1.0
# GroupID
# MessageType
# Edge of Network Node ID
# DeviceID

 
# spBv1.0/[Group ID]/[Message Type]/[EON Node ID]/[Device ID]

def deviceSetup(group_name, edge_node_name, device_name):
      device = MqttSpbEntityDevice(group_name, edge_node_name, device_name, _DEBUG);
      device.on_message = callback_message  # Received messages
      device.on_command = callback_command  # Callback for received commands
      return device
       

# Create the spB entity object
group_name = "Group-001"
edge_node_name = "RaspPI-001"
device_name = "BME280Sensor1"
device2_name = "BME280Sensor2"

device = deviceSetup(group_name, edge_node_name, device_name) 
device2 = deviceSetup(group_name, edge_node_name, device2_name)

def deviceSetAttributes(device, description, type, version, SerialNumber,DeviceID):
    # Attributes
    device.attribures.set_value("description", description)
    device.attribures.set_value("type", type)
    device.attribures.set_value("version", version)
    device.attribures.set_value("SerialNumber", SerialNumber)
    device.attribures.set_value("DeviceID", DeviceID)

description1 = "Simple EoN Device RaspPI"
type1 = "BME280-EoND-device"
version1 = "0.01"
SerialNumber1 = "123457890"
DeviceID1 = "57890"

deviceSetAttributes(device, description1, type1, version1, SerialNumber1, DeviceID1)
    
description2 = "Simple EoN Device RaspPI"
type2 = "BME280-EoND-device"
version2 = "0.01"
SerialNumber2 = "123457891"
DeviceID2 = "57891"

deviceSetAttributes(device2, description2, type2, version2, SerialNumber2, DeviceID2)

# Set the device Attributes, Data and Commands that will be sent on the DBIRTH message --------------------------


# Data / Telemetry
def deviceSetDataValue(device, variable, value):
    device.data.set_value(variable, value) 

deviceSetDataValue(device, "temperature", 0)
deviceSetDataValue(device, "humidity", 0)

deviceSetDataValue(device2, "temperature", 0)
deviceSetDataValue(device2, "humidity", 0)

# Commands
def deviceSetCommandValue(device, variable, value):
    device.commands.set_value(variable, value) 

deviceSetCommandValue(device, "rebirth", True)
deviceSetCommandValue(device2, "rebirth", True)

# Connect to the broker --------------------------------------------
def deviceConnect(device):
     _connected = False
     while not _connected:
         print("Trying to connect to broker...")
         _connected = device.connect("localhost", 1883)
    #_connected = device2.connect("localhost", 1883)
         if not _connected:
             print("  Error, could not connect. Trying again in a few seconds ...")
             time.sleep(3)
    # Send birth message
     device.publish_birth()

deviceConnect(device)
deviceConnect(device2)

def devicePublishData(device, variable1, value1, variable2, value2):
    device.data.set_value(variable1,value1)
    device.data.set_value(variable2, value2)
    device.publish_data()
    

# Send some telemetry values ---------------------------------------
value = 0  # Simple counter
for i in range(10):
    # Update the data value

    if raspPI:
        temperature = bme280.temperature
        humidity = bme280.relative_humidity 
        temperature2 = bme280_2.temperature
        humidity2 = bme280_2.relative_humidity 
    else:
        temperature = random.randint(20, 50)
        humidity = random.randint(0, 100)
        temperature2 = random.randint(20, 50)
        humidity2 = random.randint(0, 100)

    devicePublishData(device, "temperture", temperature, "humidity", humidity)
    devicePublishData(device2, "temperture", temperature2, "humidity", humidity2)

    # Send data values
    #print("Sending data - value : %d" % value)
    print("Sending data - value : temperature: %0.3f C   " % temperature)
    print("Sending data - value : humidity: %0.3f %% " %  humidity)
    print("Sending data - value : temperature2: %0.3f C   " % temperature2)
    print("Sending data - value : humidity2: %0.3f %% " %  humidity2)

    # Increase counter
    value += 1

    # Sleep some time
    time.sleep(5)

# Disconnect device -------------------------------------------------
# After disconnection the MQTT broker will send the entity DEATH message.
print("Disconnecting device")
device.disconnect()
device2.disconnect()

print("Application finished !")


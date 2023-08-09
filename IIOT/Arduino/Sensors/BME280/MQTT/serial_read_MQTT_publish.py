#!/usr/bin/env python3
##############
## Script listens to serial port and writes contents into a file
##############
## requires pySerial to be installed
import time
import os
import random
import time
import json

import serial
from datetime import datetime
from paho.mqtt import client as mqtt_client

broker = '127.0.0.1'
port = 1883
#topic = "CESMII/mqtt"
topic = "house/sensor/machine1"
client_id = f'CESMII-mqtt-{random.randint(0, 1000)}'

sensor = "BME280"
serialPort = '/dev/cu.usbmodem14401'
baudRate = 9600 #In arduino, Serial.begin(baud_rate)

# ser.readline().decode().strip()
arduino = True
#ser = serial.Serial(serialPort, baudRate)
#line = ser.readline().decode("utf-8").strip() #read until newline

if arduino:
   #ser = serial.Serial(serialPort, baudRate)
   try:
       ser = serial.Serial(serialPort, baudRate)
   except serial.SerialException as var :
       print('An Exception Occured')
       print('Exception Details-> ', var)
   else:
       print('Serial Port Opened')
       line = ser.readline().decode("utf-8").strip() #read until newline

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    #client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    msg_count = 0
    sensor_data = {'env_temperature': 0, 'env_humidity': 0, 'env_pressure': 0, 'env_altitude': 0}

    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        if arduino:
            line = ser.readline().decode("utf-8").strip() #read until newline
            lineSplit = line.split(",") #split the line into a list

            #Parse float values and assign variables from the list:
            sensor_data['env_temperature'] = float(lineSplit[0])
            sensor_data['env_pressure'] = float(lineSplit[1])
            sensor_data['env_altitude'] = float(lineSplit[2])
            sensor_data['env_humidity'] = float(lineSplit[3])
            #sensor_data['env_temperature'] = ser.readline().decode("utf-8").strip()
            #sensor_data['env_pressure'] = ser.readline().decode("utf-8").strip()
            #sensor_data['env_altitude'] = ser.readline().decode("utf-8").strip()
            #sensor_data['env_humidity'] = ser.readline().decode("utf-8").strip()
        else:
            sensor_data['env_temperature'] = round(random.uniform(10.0, 100.0),3)
            sensor_data['env_pressure'] = round(random.uniform(900.0, 1000.0),3)
            sensor_data['env_altitude'] = round(random.uniform(150.0, 300.0),3)
            sensor_data['env_humidity'] = round(random.uniform(0.0, 100.0),3)

        #print("Humidity : %.2f, \t Temperature (F) : %.2f \t Pressure (hPa) : %.2f \t Altitude (m) : %.2f \n "
        #               %(sensor_data['env_humidity'], sensor_data['env_temperature'], sensor_data['env_pressure'], sensor_data['env_altitude']))
        result = client.publish(topic, json.dumps(sensor_data))
        status = result[0]
        if status == 0:
            #print(f"Send `{msg}` to topic `{topic}`")
            print(f"Send `{sensor_data}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1
def run(): 
    client = connect_mqtt()
    client.loop_start() 
    publish(client)

if __name__ == '__main__':
    run()



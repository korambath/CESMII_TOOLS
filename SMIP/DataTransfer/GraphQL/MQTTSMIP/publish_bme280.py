#!/usr/bin/env python3
# python 3.6
import credentials

import os
import random
import time
import json


import board
from adafruit_bme280 import basic as adafruit_bme280
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)


from paho.mqtt import client as mqtt_client


broker = credentials.broker
port = 1883
topic = "CESMII/mqtt"
# generate client ID with pub prefix randomly
client_id = f'CESMII-mqtt-{random.randint(0, 1000)}'
username = credentials.username
password = credentials.password

rasppi = True

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    msg_count = 0
    sensor_data = {'env_temperature': 0, 'env_humidity': 0, 'env_pressure': 0, 'env_altitude': 0, 'cpu_temperature': 0}

    while True:
        time.sleep(2)
        msg = f"messages: {msg_count}"

        if rasppi:
            temp = os.popen("/usr/bin/vcgencmd measure_temp").read()
            cpu_temperature = float(temp[5:9]) 
            sensor_data['cpu_temperature'] = cpu_temperature

            bme280.sea_level_pressure = 1013.25

            #print("Altitude = %0.2f meters" % bme280.altitude)
            temperature = round(bme280.temperature, 3)
            humidity  = round(bme280.humidity, 3)
            pressure = round(bme280.pressure, 3)
            altitude = round(bme280.altitude, 3)
            
            sensor_data['env_temperature'] = temperature
            sensor_data['env_humidity'] = humidity
            sensor_data['env_pressure'] = pressure
            sensor_data['env_altitude'] = altitude
            print("Temperature (F): %.2f, \t Humidity  : %.2f \t Pressure (hPa) : %.2f \t Altitude (m) : %.2f \t cpu_temperature (C) : %.2f \n "\
                      %(temperature, humidity, pressure, altitude, cpu_temperature ))


        else:
            temp6 = open("/sys/class/thermal/thermal_zone5/temp", "r")
            data = float(temp6.read())/1000
            temp6.close()
            #temp = os.popen("/opt/vc/bin/vcgencmd measure_temp").read()
            sensor_data['cpu_temperature'] = data
            temp7 = open("/sys/class/thermal/thermal_zone9/temp", "r")
            data = float(temp7.read())/1000
            temp7.close()
            sensor_data['temperature7'] = data

        #result = client.publish(topic, msg)
        result = client.publish(topic, json.dumps(sensor_data))
        # result: [0, 1]
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

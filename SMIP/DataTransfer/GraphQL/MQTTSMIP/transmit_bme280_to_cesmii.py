# python3.6
import credentials

from datetime import datetime
from smip import graphql
import requests
import uuid
import json
import time

import random

from paho.mqtt import client as mqtt_client


# for MQTT Broker credentials from credentials.py
# Replace the port number and topic as well.

broker = credentials.broker
port = 1883
topic = "CESMII/mqtt"
# generate client ID with pub prefix randomly
client_id = f'CESMII-mqtt-{random.randint(0, 100)}'

username = credentials.username
password = credentials.password


# for CESMII SMIP
authenticator= credentials.authenticator
password_smip= credentials.password_smip
name= credentials.name
role= credentials.role
url= credentials.url

# Connection information for your SMIP Instance GraphQL endpoint
graphql = graphql(authenticator, password_smip, name, role, url)

# Here we are sending 5 attributes edit accordingly

write_attribute_id1 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id2 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id3 = "REPLACE"     #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id4 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id5 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model

print (f"Listening for MQTT messages on topic: {topic} ...")


def make_datetime_utc():
        utc_time = str(datetime.utcnow())
        time_parts = utc_time.split(" ")
        utc_time = "T".join(time_parts)
        time_parts = utc_time.split(".")
        utc_time = time_parts[0] + "Z"
        return utc_time

def update_smip(value1, value2, value3, value4,value5):
        print("Posting Data to CESMII Smart Manufacturing Platform...")
        print()
        utc_time=make_datetime_utc()
        time.sleep(2)
        #input: {{attributeOrTagId: "{write_attribute_id}", entries: [ {{timestamp: "{make_datetime_utc()}", value: "{sample_value}", status: "1"}} ] }}
        smp_query = f"""
                mutation updateTimeSeries {{
                ts1: replaceTimeSeriesRange(
                    input: {{attributeOrTagId: "{write_attribute_id1}"  
                     entries: [ {{timestamp: "{utc_time}", value: "{value1}", status: "0"}} ] }}
                    ) 
                    {{
                       json
                    }}
                ts2: replaceTimeSeriesRange(
                    input: {{attributeOrTagId: "{write_attribute_id2}"
                       entries: [ {{timestamp: "{utc_time}", value: "{value2}", status: "0"}} ] }}
                    ) 
                    {{
                       json
                    }}
                ts3: replaceTimeSeriesRange(
                    input: {{attributeOrTagId: "{write_attribute_id3}"
                         entries: [ {{timestamp: "{utc_time}", value: "{value3}", status: "0"}} ] }}
                    ) 
                    {{
                       json
                    }}
                ts4: replaceTimeSeriesRange(
                    input: {{attributeOrTagId: "{write_attribute_id4}" 
                        entries: [ {{timestamp: "{utc_time}", value: "{value4}", status: "0"}} ] }}
                    ) 
                    {{
                       json
                    }}
                ts5: replaceTimeSeriesRange(
                    input: {{attributeOrTagId: "{write_attribute_id5}"
                       entries: [ {{timestamp: "{utc_time}", value: "{value5}", status: "0"}} ] }}
                    ) 
                    {{
                       json
                    }}
                }}
            """
        smp_response = ""

        try:
                smp_response = graphql.post(smp_query)
        except requests.exceptions.HTTPError as e:
                print("An error occured accessing the SM Platform!")
                print(e)

        print("Response from SM Platform was...")
        print(json.dumps(smp_response, indent=2))
        print()




def connect_mqtt() -> mqtt_client:
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


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        data = str(msg.payload.decode("utf-8"))
        res = json.loads(data)
        temp1 = str(res['env_temperature'])
        temp2 = str(res['env_humidity'])
        temp3 = str(res['env_pressure'])
        temp4 = str(res['env_altitude'])
        temp5 = str(res['cpu_temperature'])
        print(temp1, temp2, temp3, temp4, temp5)
        update_smip(temp1, temp2, temp3, temp4, temp5)


    client.subscribe(topic)
    client.on_message = on_message


def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()



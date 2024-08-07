# python3.6
import credentials

from datetime import datetime
#import paho.mqtt.client as mqtt
from smip import graphql
import requests
import uuid
import json
import time

import random
from random import randint


authenticator= credentials.authenticator
password_smip= credentials.password_smip
name= credentials.name
role= credentials.role
url= credentials.url

# Connection information for your SMIP Instance GraphQL endpoint
graphql = graphql(authenticator, password_smip, name, role, url)

write_attribute_id1 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id2 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id3 = "REPLACE"     #The Equipment Attribute ID to be updated in your SMIP model



def make_datetime_utc():
        utc_time = str(datetime.utcnow())
        time_parts = utc_time.split(" ")
        utc_time = "T".join(time_parts)
        time_parts = utc_time.split(".")
        utc_time = time_parts[0] + "Z"
        return utc_time

def update_smip(value1, value2, value3):
        print("Posting Data to CESMII Smart Manufacturing Platform...")
        print()
        utc_time=make_datetime_utc()
        #time.sleep(5)
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





def run():
    while True:
        temperature = round( random.uniform(22.0, 28.0), 3)
        humidity  = round( random.uniform(20.0, 60.0), 3)
        pressure = round( random.uniform(700.0, 1000.0), 3)
        #temperature = randint(10,60)
        #pressure = randint(200,999)
        #humidity = randint(0,100)
        print(temperature, pressure, humidity)
        print("Temperature (F): %.2f \t Pressure (hPa) : %.2f \t Humidity  : %.2f \n"%(temperature, pressure, humidity  ))
        update_smip(temperature, pressure, humidity)
        time.sleep(2)




if __name__ == '__main__':
    run()



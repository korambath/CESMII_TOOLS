import paho.mqtt.client as mqtt #import the client1
import time, json, random
from datetime import datetime, timezone
from random import randrange, uniform



broker_address="127.0.0.1"
port = 1883
#client_id="P2"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
topic = "house/sensor/machine1"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
       print("Connected to MQTT Broker!")
       print("Connected with result code "+str(rc))
    else:
       print("Failed to connect, return code %d\n", rc)

    print("Subscribing to topic ", topic)
    client.subscribe(topic)


def on_log(client, userdata, level, buffer):
     print("Log ", buffer)


def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))



############
def on_message(client, userdata, msg):
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    print("message qos=",msg.qos)
    #print("message retain flag=",msg.retain)

    #print("message received  ",str(msg.payload.decode("utf-8")),\
    #      "message topic",msg.topic,"retained message flag ",msg.retain)
    if msg.retain==1:
        print("This is a retained message")

    #data = str(msg.payload.decode("utf-8"))
    #print(data)
    msg = str(msg.payload.decode("utf-8"))
    sensor_data = json.loads(msg)
    machine_id  =  sensor_data['machine_id'] 
    temperature =  sensor_data['temperature'] 
    pressure    =  sensor_data['pressure'] 
    humidity    =  sensor_data['humidity'] 

    recorded_day = sensor_data['date']
    seconds = sensor_data['seconds']

    print(f'Sensor data revieved from: {machine_id}')
    print(f'Temperature = {temperature}')
    print(f'pressure    = {pressure}')
    print(f'humidity    = {humidity}')

    print(f"Recorded on {recorded_day}:{seconds}")





########################################


def run():
    print("creating new instance")
    client = mqtt.Client(client_id)
    client.on_connect = on_connect


    client.on_message = on_message  #attach function to callback
    #client.on_log = on_log
    #client.on_subscribe = on_subscribe

    print("connecting to broker")
    client.connect(broker_address, port)
    client.loop_forever()


#client.loop_start() #start the loop
#client.loop_stop() #stop the loop


    time.sleep(4)



if __name__ == '__main__':
    run()


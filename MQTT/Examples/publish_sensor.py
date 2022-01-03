import paho.mqtt.client as mqtt #import the client1
import time, json, random
from datetime import datetime, timezone
from random import randrange, uniform

broker_address="127.0.0.1"
port = 1883
#client_id="P1"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 1000)}'
topic = "house/sensor/machine1"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)


def on_log(client, userdata, level, buffer):
     print("Log ", buffer)


def on_publish(client,userdata,result):             #create function for callback
    print(f"data published  {result} \n")
    pass

def publish(client):
    machine_id=1111
    msg_count = 0
    #sensor_data = {'temperature6': 0, 'temperature7': 0}
    sensor_data = {}
    sensor_data['machine_id'] = machine_id
    while True:
        time.sleep(4)
        #msg = f"messages: {msg_count}"
        data = uniform(40.0, 80.0)
        data = round(data, 2)
        sensor_data['temperature'] = data
        data = uniform(60.0, 1000.0)
        data = round(data, 2)
        sensor_data['pressure'] = data
        data = uniform(10.0, 100.0)
        data = round(data, 2)
        sensor_data['humidity'] = data

        now = datetime.now()
        print(now)
        totaltime = now.hour*3600 + now.minute*60 + now.second
        #totaltime = now.timestamp() # time since epoch
        date = datetime.now().date()
        sensor_data['date'] = str(date)
        sensor_data['seconds'] = totaltime

        #result = client.publish(topic, msg) # publish method returns a tuple (result, mid).
        #                                    # A result of 0 indicates success.
        #                                    # mid value is an integer that corresponds to the published message number
        result = client.publish(topic, json.dumps(sensor_data))
        # result: [0, 1]
        status = result[0]
        if status == 0:
            #print(f"Iter: {result[1]} Send `{msg}` to topic `{topic}`")
            #print(result[1])
            print(f"Send message {msg_count} `{sensor_data}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1



def run():
    print("creating new instance")
    client = mqtt.Client(client_id)

    #client.on_log = on_log # Debug

    
    client.on_connect = on_connect
    print("connecting to broker")
    client.connect(broker_address, port)

    client.loop_start()
    #client.on_publish = on_publish      #assign function to callback
    print("Publishing to topic ", topic)
    publish(client)

#client.loop_start() #start the loop
#client.loop_stop() #stop the loop


if __name__ == '__main__':
    run()


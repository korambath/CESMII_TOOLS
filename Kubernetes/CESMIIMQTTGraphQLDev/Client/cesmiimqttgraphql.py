import argparse
import requests
import json
import time
from datetime import datetime
from random import uniform
import paho.mqtt.client as mqtt

MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = "Envsensor/data"  # Replace with your topic
# Initialize a message counter
msg_count = 0



class SMIPClient:
    def __init__(self, authenticator, password, name, role, url, write_attribute_ids):
        self.authenticator = authenticator
        self.password = password
        self.name = name
        self.role = role
        self.url = url
        self.write_attribute_ids = write_attribute_ids
        self.bearer_token = "Bearer eyJ"  # Placeholder for the actual token

    def perform_graphql_request(self, query, headers=None):
        try:
            response = requests.post(self.url, headers=headers, json={"query": query})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error performing GraphQL request: {e}")
            raise

    def get_bearer_token(self):
        query = f"""
        mutation authRequest {{
            authenticationRequest(input: {{authenticator: "{self.authenticator}", role: "{self.role}", userName: "{self.name}"}}) {{
                jwtRequest {{
                    challenge
                    message
                }}
            }}
        }}
        """
        response = self.perform_graphql_request(query)
        jwt_request = response['data']['authenticationRequest']['jwtRequest']
        
        if not jwt_request['challenge']:
            raise requests.exceptions.HTTPError(jwt_request['message'])
        
        print(f"Challenge received: {jwt_request['challenge']}")
        
        query = f"""
        mutation authValidation {{
            authenticationValidation(input: {{authenticator: "{self.authenticator}", signedChallenge: "{jwt_request['challenge']}|{self.password}"}}) {{
                jwtClaim
            }}
        }}
        """
        response = self.perform_graphql_request(query)
        jwt_claim = response['data']['authenticationValidation']['jwtClaim']
        self.bearer_token = f"Bearer {jwt_claim}"

    def make_datetime_utc(self):
        return datetime.utcnow().isoformat() + "Z"

    def update_smip(self, values):
        print("Posting Data to CESMII Smart Manufacturing Platform...\n")
        utc_time = self.make_datetime_utc()
        
        queries = [
            f"""
            ts{index + 1}: replaceTimeSeriesRange(
                input: {{attributeOrTagId: "{self.write_attribute_ids[index]}",
                entries: [{{timestamp: "{utc_time}", value: "{value}", status: "0"}}]}}
            ) {{
                json
            }}
            """ for index, value in enumerate(values)
        ]
        
        return f"mutation updateTimeSeries {{{' '.join(queries)}}}"

    def do_query(self, query):
        headers = {"Authorization": self.bearer_token}
        
        try:
            response = self.perform_graphql_request(query, headers)
            print("Response from SM Platform:\n")
            print(json.dumps(response, indent=2))
            return response
        except requests.exceptions.HTTPError as e:
            if "forbidden" in str(e).lower() or "unauthorized" in str(e).lower():
                print("Bearer Token expired! Attempting to retrieve a new GraphQL Bearer Token...\n")
                self.get_bearer_token()
                print("New Token received:\n")
                response = self.perform_graphql_request(query, headers={"Authorization": self.bearer_token})
                print("Response from SM Platform:\n")
                print(json.dumps(response, indent=2))
                return response
            else:
                print("An error occurred accessing the SM Platform!")
                print(e)
                raise

def parse_arguments():
    parser = argparse.ArgumentParser(description="CESMII Smart Manufacturing Platform Data Sender")
    parser.add_argument("-a", "--authenticator", type=str, default="YourAuthenticatorName", help="Authenticator Name")
    parser.add_argument("-p", "--password", type=str, default="YourAuthenticatorPassword", help="Authenticator Password")
    parser.add_argument("-n", "--name", type=str, default="YourAuthenticatorBoundUserName", help="Authenticator Bound User Name")
    parser.add_argument("-r", "--role", type=str, default="YourAuthenticatorRole", help="Authenticator Role")
    parser.add_argument("-u", "--url", type=str, default="instance_graphql_endpoint", help="GraphQL URL")
    parser.add_argument("-i", "--ids", type=str, nargs=3, default=["73309", "73311", "73313"], help="List of write attribute IDs")
    parser.add_argument("-m", "--mqtt_broker", type=str, default="mqtt.example.com", help="MQTT Broker")
    parser.add_argument("-t", "--mqtt_topic", type=str, default="your/topic", help="MQTT Topic")
    return parser.parse_args()

def on_message(client, userdata, msg):
    data = msg.payload.decode('utf-8')
    print(f"Received MQTT message: {data}")
    global msg_count
    msg_count += 1  # Increment the message counter

    
    try:
        values = json.loads(data)  # Assuming the incoming MQTT message is a JSON object
        print(f" values = {values}")
        temperature = values.get("temperature")
        humidity = values.get("humidity")
        pressure = values.get("pressure")
        #print(f" temperature = {temperature} humidity = {humidity} pressure = {pressure}")
        now = datetime.now()
        print(f"Message {msg_count} received {msg.topic} :  temperature: {temperature}°C, humidity: {humidity}%, pressure: {pressure} mbar at {now} ")
        #mutation_string = smip_client.update_smip(values)
        mutation_string = smip_client.update_smip([temperature, pressure, humidity])
        smip_client.do_query(mutation_string)
    except json.JSONDecodeError:
        print("Failed to decode JSON from MQTT message.")

def main():
    global smip_client  # Declare as global for access in on_message
    args = parse_arguments()
    print(f"Authenticator: {args.authenticator} password: {args.password} name: {args.name} role: {args.role} \
               url: {args.url} ids: {args.ids} topic: {args.mqtt_topic} broker: {args.mqtt_broker}")
 
    smip_client = SMIPClient(
        authenticator=args.authenticator,
        password=args.password,
        name=args.name,
        role=args.role,
        url=args.url,
        write_attribute_ids=args.ids
    )

    # Set up MQTT client
    mqtt_client = mqtt.Client()
    mqtt_client.on_message = on_message
    mqtt_client.connect(args.mqtt_broker, MQTT_PORT, 60)
    #mqtt_client.connect(args.mqtt_broker)
    mqtt_client.subscribe(args.mqtt_topic)

    # Start the MQTT client loop in a separate thread
    mqtt_client.loop_start()

    # Retrieve initial Bearer Token
    smip_client.get_bearer_token()

    try:
        while True:
            time.sleep(1)  # Keep the main thread alive
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        mqtt_client.loop_stop()

if __name__ == '__main__':
    main()


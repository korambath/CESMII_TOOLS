import argparse
import os
import requests
import json
import time
from datetime import datetime
from random import uniform

def print_data(data, client, indent=0):
    """ Recursively prints data (handles nested lists and dictionaries) """
    if isinstance(data, dict):
        print(json.dumps(data, indent=4))

        #for key, value in data.items():
        #    print(f"{key}: {value}")
        #for key, value in data.items():
            # Print the key-value pair with proper indentation
        #    print(' ' * indent + f"{key}:")
        #    print_data(value, client, indent + 2)  # Recurse into the value
        event_type      = data.get("event_type")
        mitre_threat_no = data.get("mitre_threat_no")
        description     = data.get("description") 
        event_time      = data.get("timestamp") 
        now = datetime.now()


        if mitre_threat_no:
           print(f"Message received: event type: {event_type}, "
                 f"mitre_threat_no: {mitre_threat_no}, description: {description}, "
                 f"timestamp: {event_time} at {now}")
           #print(f"Message received :  event type: {event_type}, mitre_threat_no: {mitre_threat_no}, description: {description}, timestamp: {event_time} at {now} \n ")
           mutation_string = client.update_smip([event_type, mitre_threat_no, description, event_time])
           client.do_query(mutation_string)
 
    elif isinstance(data, list):
        for i, item in enumerate(data):
            print(' ' * indent + f"Item {i + 1}:")
            print_data(item, client,  indent + 2)  # Recurse into the list item
    else:
        # Print the value if it's not a dictionary or list
        print(' ' * indent + f"{data}")


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
    parser.add_argument("-s", "--server", type=str, default="localhost", help="The base URL of the HTTP server")
    parser.add_argument("-t", "--port", type=int, default=8000, help="The port number of the HTTP server ")
    parser.add_argument("-i", "--ids", type=str, nargs=4, default=["73309", "73311", "73313"], help="List of write attribute IDs")
    return parser.parse_args()

def main():
    args = parse_arguments()
    client = SMIPClient(
        authenticator=args.authenticator,
        password=args.password,
        name=args.name,
        role=args.role,
        url=args.url,
        write_attribute_ids=args.ids
    )
    # Construct the full URL by combining the base URL and port
    full_url = f"http://{args.server}:{args.port}"
    print(f" HTTP Server URL: {full_url} \n")

    # Infinite loop to continuously poll the server for new data
    while True:
        try:
            # Send GET request to retrieve the data that has been sent to the server
            response = requests.get(full_url)

            if response.status_code == 200:
                data = response.json()  # Get the response data (JSON)
                if data:
                    print("New data received from the server:")

                    print_data(data, client)  # Print the received data recursively
                else:
                    print("No new data received yet.")

            else:
                print(f"Error: {response.status_code}")
                print(response.text)

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

        # Sleep for a few seconds before checking again (adjust as needed)
        time.sleep(5)


if __name__ == '__main__':
    main()


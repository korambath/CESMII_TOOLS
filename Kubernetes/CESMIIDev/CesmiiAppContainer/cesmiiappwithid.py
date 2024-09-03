import argparse
import os
import requests
import json
import time
from datetime import datetime
from random import uniform

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
    parser.add_argument("-i", "--ids", type=str, nargs=3, default=["10009", "10011", "10013"], help="List of write attribute IDs")
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

    while True:
        temperature = round(uniform(22.0, 28.0), 3)
        humidity = round(uniform(20.0, 60.0), 3)
        pressure = round(uniform(700.0, 1000.0), 3)
        print(f"Temperature (°C): {temperature:.2f} \t Pressure (hPa): {pressure:.2f} \t Humidity: {humidity:.2f}\n")
        
        mutation_string = client.update_smip([temperature, pressure, humidity])
        client.do_query(mutation_string)
        time.sleep(2)

if __name__ == '__main__':
    main()


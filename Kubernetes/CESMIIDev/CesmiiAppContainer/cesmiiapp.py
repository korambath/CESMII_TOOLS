import argparse
import os

from datetime import datetime
#import smip
#from smip import graphql
import requests
import json
import time

import random
from random import randint



write_attribute_id1 = "REPLACE"
write_attribute_id2 = "REPLACE"
write_attribute_id3 = "REPLACE"


current_bearer_token = "Bearer eyJ"


''' These values come from your Authenticator, which you configure in the Developer menu > GraphQL Authenticator
Rather than binding this connectivity directly to a user, we bind it to an Authenticator, which has its own
credentials. The Authenticator, in turn, is linked to a user -- sort of like a Service Principle.
In the Authenticator setup, you will also configure role, and Token expiry. '''
parser = argparse.ArgumentParser()

parser.add_argument("-a", "--authenticator", type=str, default="YourAuthenticatorName", help="Authenticator Name")
parser.add_argument("-p", "--password", type=str, default="YourAuthenticatorPassword", help="Authenticator Password")
parser.add_argument("-n", "--name", type=str, default="YourAuthenticatorBoundUserName", help="Authenticator Bound User Name")
parser.add_argument("-r", "--role", type=str, default="YourAuthenticatorRole", help="Authenticator Role")
parser.add_argument("-u", "--url", type=str, default="instance_graphql_endpoint", help="GraphQL URL")
args = parser.parse_args()


    # Retrieve environment variables if they exist
authenticator = os.getenv('AUTHENTICATOR', args.authenticator)
password = os.getenv('PASSWORD', args.password)
name = os.getenv('USERNAME', args.name)
role = os.getenv('ROLE', args.role)
url = os.getenv('URL', args.url)
    
# Simulate application logic
print(f"Username: {name}")
print(f"Password: {password}")
print(f"Authenticator: {authenticator}")

print(f"Role: {role}")
print(f"URL: {url}")

def perform_graphql_request(content, url=args.url, headers=None):
    #print("Performing request with content: ")
    #print(content)

    r = requests.post(url, headers=headers, data={"query": content})
    r.raise_for_status()
    return r.json()

def get_bearer_token (auth=args.authenticator, password=args.password, name=args.name, url=args.url, role=args.role):
    response = perform_graphql_request(f"""
      mutation authRequest {{
        authenticationRequest(
          input: {{authenticator: "{auth}", role: "{role}", userName: "{name}"}}
        ) {{
          jwtRequest {{
            challenge, message
          }}
        }}
      }}
    """)
    jwt_request = response['data']['authenticationRequest']['jwtRequest']
    if jwt_request['challenge'] is None:
        raise requests.exceptions.HTTPError(jwt_request['message'])
    else:
        print("Challenge received: " + jwt_request['challenge'])
        response=perform_graphql_request(f"""
          mutation authValidation {{
            authenticationValidation(
              input: {{authenticator: "{auth}", signedChallenge: "{jwt_request["challenge"]}|{password}"}}
              ) {{
              jwtClaim
            }}
          }}
      """)
    jwt_claim = response['data']['authenticationValidation']['jwtClaim']
    return f"Bearer {jwt_claim}"

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
                }}
            """

        return smp_query
def do_query(smp_query):
  global current_bearer_token
  print("Posting Data from CESMII Smart Manufacturing Platform...")
  print()

  ''' Request some data -- this is an equipment query.
        Use Graphiql on your instance to experiment with additional queries
        Or find additional samples at https://github.com/cesmii/API/blob/main/Docs/queries.md '''
#  smp_query = """
#    {
#      equipments {
#        id
#        displayName
#      }
#    }"""
  smp_response = ""

  try:
    #Try to request data with the current bearer token
    smp_response = perform_graphql_request(smp_query, headers={"Authorization": current_bearer_token})
    print("Response from SM Platform was...")
    print(json.dumps(smp_response, indent=2))
    print()
  except requests.exceptions.HTTPError as e:
    # 403 Client Error: Forbidden for url: https://demo.cesmii.net/graphql
    #print(e)
    if "forbidden" in str(e).lower() or "unauthorized" in str(e).lower():
      print("Bearer Token expired!")
      print("Attempting to retreive a new GraphQL Bearer Token...")
      print()

      #Authenticate
      current_bearer_token = get_bearer_token()

      #print("New Token received: " + current_bearer_token)
      print("New Token received: " )
      print()

      #Re-try our data request, using the updated bearer token
      # TODO: This is a short-cut -- if this subsequent request fails, we'll crash. You should do a better job :-)
      smp_response = perform_graphql_request(smp_query, headers={"Authorization": current_bearer_token})
      print("Response from SM Platform was...")
      print(json.dumps(smp_response, indent=2))
      print()
    else:
      print("An error occured accessing the SM Platform!")
      print(e)
      exit(-1)

  return smp_response



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
        mutation_string = update_smip(temperature, pressure, humidity)
        smp_response = do_query(str(mutation_string))
        time.sleep(2)


if __name__ == '__main__':
    run()


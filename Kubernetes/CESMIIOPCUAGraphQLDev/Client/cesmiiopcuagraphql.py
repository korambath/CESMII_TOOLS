import argparse
import asyncio
import logging
import json
from datetime import datetime
import requests
from asyncua import Client, Node

msg_count=0

class SMIPClient:
    def __init__(self, authenticator: str, password: str, name: str, role: str, url: str, write_attribute_ids: list[str]):
        self.authenticator = authenticator
        self.password = password
        self.name = name
        self.role = role
        self.url = url
        self.write_attribute_ids = write_attribute_ids
        self.bearer_token = "Bearer eyJ"  # Placeholder for the actual token
        self.logger = logging.getLogger(__name__)

    def perform_graphql_request(self, query: str, headers: dict = None) -> dict:
        try:
            response = requests.post(self.url, headers=headers, json={"query": query})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error("Error performing GraphQL request: %s", e)
            raise

    def get_bearer_token(self):
        self.logger.info("Requesting Bearer Token...")
        print("Requesting Bearer Token...")
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
        
        self.logger.info("Challenge received: %s", jwt_request['challenge'])
        print("Challenge received: %s", jwt_request['challenge'])
        
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
        self.logger.info("New Bearer Token received.")
        print("New Bearer Token received.")

    def make_datetime_utc(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def update_smip(self, values: list[float]) -> str:
        self.logger.info("Posting Data to CESMII Smart Manufacturing Platform...")
        print("Posting Data to CESMII Smart Manufacturing Platform...")
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

    def do_query(self, query: str):
        headers = {"Authorization": self.bearer_token}
        
        try:
            response = self.perform_graphql_request(query, headers)
            self.logger.info("Response from SM Platform:\n%s", json.dumps(response, indent=2))
            print("Response from SM Platform:\n%s", json.dumps(response, indent=2))
            return response
        except requests.exceptions.HTTPError as e:
            if "forbidden" in str(e).lower() or "unauthorized" in str(e).lower():
                self.logger.warning("Bearer Token expired! Attempting to retrieve a new token...")
                self.get_bearer_token()
                return self.do_query(query)
            else:
                self.logger.error("An error occurred accessing the SM Platform: %s", e)
                raise


async def browse_children(objects: Node) -> tuple[list[str], list[float]]:
    """Browse child nodes and return their browse names and values."""
    children = await objects.get_children()
    var_list, val_list = [], []

    for child in children:
        browse_name = await child.read_browse_name()
        value = await child.read_value()
        var_list.append(browse_name.Name)
        val_list.append(value)
        
    return var_list, val_list

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CESMII Smart Manufacturing Platform Data Sender")
    parser.add_argument("-a", "--authenticator", type=str, default="YourAuthenticatorName", help="Authenticator Name")
    parser.add_argument("-p", "--password", type=str, default="YourAuthenticatorPassword", help="Authenticator Password")
    parser.add_argument("-n", "--name", type=str, default="YourAuthenticatorBoundUserName", help="Authenticator Bound User Name")
    parser.add_argument("-r", "--role", type=str, default="YourAuthenticatorRole", help="Authenticator Role")
    parser.add_argument("-u", "--graphurl", type=str, default="instance_graphql_endpoint", help="GraphQL URL")
    parser.add_argument("-i", "--ids", type=str, nargs=3, default=["73309", "73311", "73313"], help="List of write attribute IDs")
    parser.add_argument("-o", "--opcurl", type=str, default="opc.tcp://192.168.1.3:4840/freeopcua/server/", help="OPC UA URL")
    return parser.parse_args()

async def main() -> None:
    args = parse_arguments()
    print(f"Authenticator: {args.authenticator} name: {args.name} role: {args.role}")
    print(f"url: {args.graphurl} ids: {args.ids} OPCUAURL: {args.opcurl} ")
    global msg_count

    
    logging.basicConfig(level=logging.INFO)
    smip_client = SMIPClient(
        authenticator=args.authenticator,
        password=args.password,
        name=args.name,
        role=args.role,
        url=args.graphurl,
        write_attribute_ids=args.ids
    )

    logger = logging.getLogger(__name__)
    logger.info("Connecting to %s ...", args.opcurl)
    print("Connecting to %s ...", args.opcurl)

    async with Client(url=args.opcurl) as client:
        root = client.get_root_node()
        logger.info("Objects node is: %s", root)
        namespace = "http://examples.freeopcua.github.io"
        objectname = "WeatherObject"
        logger.info('Namespace: %s, URL: %s, Object Name: %s.', namespace, args.opcurl, objectname)
        print('Namespace: %s, URL: %s, Object Name: %s.', namespace, args.opcurl, objectname)

        idx = await client.get_namespace_index(namespace)
        weather_obj = await client.get_objects_node().get_child([f'{idx}:{objectname}'])
        logger.info("%s Node is: %s", objectname, weather_obj)
        print("%s Node is: %s", objectname, weather_obj)

        while True:
            var_list, val_list = await browse_children(weather_obj)
            message = dict(zip(var_list, val_list))
            json_data = json.dumps(message, indent=3)
            print(json_data)

            print(message)
            now = datetime.now()

            logger.info("Temperature: %s, Humidity: %s, Pressure: %s", message.get('Temperature'), message.get('Humidity'), message.get('Pressure'))
            print(f"Msg: {msg_count}  Temperatue: {message.get('Temperature')} Pressure: {message.get('Pressure')} Humidity: {message.get('Temperature')} at {now}")

            mutation_string = smip_client.update_smip([message.get("Temperature"), message.get("Pressure"), message.get("Humidity")])
            smip_client.do_query(mutation_string)

            msg_count += 1  # Increment the message counter
            await asyncio.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.CRITICAL)
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error("An error occurred: %s", e)


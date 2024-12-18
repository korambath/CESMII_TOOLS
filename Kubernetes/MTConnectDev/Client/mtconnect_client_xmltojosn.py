import argparse
import requests
import xmltodict
import json

def parse_arguments():
    parser = argparse.ArgumentParser(description="CESMII Smart Manufacturing Platform Data Sender")
    parser.add_argument("-u", "--mt_url", type=str, default="http://localhost", help="MT Connect Server")
    parser.add_argument("-p", "--mt_port", type=str, default="5000", help="MT Connect Port")
    return parser.parse_args()


# Function to fetch data from the server
def fetch_mtconnect_data(url):
    #url = "http://localhost:5000/current_data"  # Replace with your server URL
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Parse the XML response
            xml_data = response.content
            # Convert XML to dictionary using xmltodict
            dict_data = xmltodict.parse(xml_data)
            
            # Convert the dictionary to JSON
            json_data = json.dumps(dict_data, indent=4)
            
            # Print JSON data
            print(json_data)
        else:
            print(f"Failed to fetch data: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    args = parse_arguments()
    print(f" url: {args.mt_url}  port: {args.mt_port}")

    url = args.mt_url
    port = args.mt_port
    # Construct the full URL by combining the base URL and port
    full_url = f"http://{url}:{port}/current_data"


    #url = "http://"+str(url) + ":" + str(port) + "/current_data"
    print(f" Full url: {full_url}  ")
    fetch_mtconnect_data(full_url)


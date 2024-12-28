import argparse
import requests
import json
from datetime import datetime

# Function to generate a formatted timestamp
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Function to send the POST request
def send_post_request(url, payload):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("POST request was successful")
            print(f"Response: {response.json()}")
        else:
            print(f"Failed POST request. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Send security events as a POST request to a given URL and port.")
    
    # Add arguments for URL and port
    parser.add_argument('url', type=str, help="The base URL to connect to (e.g., 'localhost').")
    parser.add_argument('port', type=int, help="The port number to connect to.")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create the full URL
    full_url = f"http://{args.url}:{args.port}/security/event"
    
    # Prepare the JSON payload
    payload = [
        {
            "event type": "Non TLS Connection",
            "mitre_threat_no": "CWE_9999",
            "description": "originated from 192.168.1.65",
            "timestamp": get_timestamp()
        },
        {
            "event type": "Unauthorised Application Access",
            "mitre_threat_no": "CWE_9999",
            "description": "originated from 192.168.1.65",
            "timestamp": get_timestamp()
        }
    ]
    
    # Send the POST request
    send_post_request(full_url, payload)

if __name__ == "__main__":
    main()


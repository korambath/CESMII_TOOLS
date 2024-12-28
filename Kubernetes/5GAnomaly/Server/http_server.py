# http_server.py

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import argparse

# In-memory storage for received POST data
received_data = []


def parse_arguments():
    parser = argparse.ArgumentParser(description="CESMII Smart Manufacturing Platform Data Sender")
    parser.add_argument("-u", "--url", type=str, default="localhost", help="REST Server")
    parser.add_argument("-p", "--port", type=str, default="8000", help="REST Port")
    return parser.parse_args()


class MyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests."""
        # Check if we have received any POST data
        if received_data:
            # Fetch the first item in the list to return it
            data_to_send = received_data.pop(0)  # Remove the first item from the list
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # Send the data and remove it from the list
            self.wfile.write(data_to_send.encode('utf-8'))
        else:
            # Send a message saying no data has been received yet
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "No data received yet"}).encode('utf-8'))
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers['Content-Length'])  # Get the length of the request data
        post_data = self.rfile.read(content_length)  # Read the data
        
        # Store the received data in memory
        received_data.append(post_data.decode('utf-8'))  # Append the decoded data to the list
        
        # Print the received payload to the server console
        print(f"Received POST data: {post_data.decode('utf-8')}")
        
        # Send a response back to the client
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "success", "message": "Payload received"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

def run(url='localhost', port=8000, server_class=HTTPServer, handler_class=MyHandler):
    server_address = (url, port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    args = parse_arguments()
    print(f" url: {args.url}  port: {args.port}")

    url = args.url
    port = int (args.port)

    run(url, port)


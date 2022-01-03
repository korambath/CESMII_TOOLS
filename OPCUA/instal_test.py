from opcua import Server

server = Server()

url = "opc.tcp://127.0.0.1:12345"
server.set_endpoint(url)


try:
    print("Start SErver")
    server.start()
    print("Server Online")
    print("Server started at {}".format(url))


finally:
    server.stop()
    print("Server Offline")


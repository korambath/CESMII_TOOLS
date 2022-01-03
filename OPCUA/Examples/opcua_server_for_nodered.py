#!/usr/bin/env python3

from opcua import Server
from random import randint
import datetime

import time


server = Server()

url = "opc.tcp://127.0.0.1:4840"
#url = "opc.tcp://192.168.1.6:4840"
#url = "opc.tcp://192.168.1.2:62548"

server.set_endpoint(url)

name = "OPCUA_SIMULATION_SERVER"

addspace = server.register_namespace(name)
print("Addspace :{}".format(addspace))

node = server.get_objects_node()

print("Node : ", node)

Param = node.add_object(addspace, "Parameters")

print("Parame :", Param)

Temp = Param.add_variable(addspace, "Temperature", 0)
Press = Param.add_variable(addspace, "Pressure", 0)
Time = Param.add_variable(addspace, "Time", 0)
state = Param.add_variable(addspace, "state of light bulb", False)


print("Temp : {} Press : {} Time : {}".format( Temp, Press, Time))

Temp.set_writable()
Press.set_writable()
Time.set_writable()
state.set_writable()

try:
    print("Start Server")
    server.start()
    print("Server Online")
    print("Server Started at {}".format(url))


    while True:
          Temperature = randint(10,50)
          Pressure = randint(200,999)
          TIME = datetime.datetime.now()
          state_value =  str(state.get_value())

          print(Temperature, Pressure, TIME, state_value )

          Temp.set_value(Temperature)
          Press.set_value(Pressure)
          Time.set_value(TIME)

          time.sleep(2)
finally:
    server.stop()
    print("Server Offline")






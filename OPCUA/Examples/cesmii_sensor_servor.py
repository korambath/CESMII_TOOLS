from time import sleep
import random
from opcua import ua, Server
import datetime

if __name__ == "__main__":
   """
       OPC-UA-Server Setup
       namespace 2: CESMII
       +-- Temperature Sensor
       |+---- Manufacturer Name
       |+---- Serial Number
       |+---- Temperature
       |+---- Time
       +-- Furnace
       |+---- Manufacturer Name
       |+---- Serial Number
       |+---- State (ON/OFF)

   """
   server = Server()
   server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

   endpoint_url = "opc.tcp://localhost:62541"
   #endpoint_url = "opc.tcp://192.168.1.6:62541"
   server.set_endpoint(endpoint_url)
   server_name="CESMII"
   server.set_server_name(server_name)
   address_space = server.register_namespace(server_name)

   print("Server address_space {}".format(address_space))

   objects=server.get_objects_node()
   print("Server objects {}".format(objects))

   temp_sensor=objects.add_object('ns=2;s="C_TS1"', "Temperature Sensor 1")
   print("Temperature Sensor Nodeid {}".format(temp_sensor))

   temp_sensor.add_variable('ns=2;s="C_TS1_ManfctrName"', "C_TS1 Manufacture Name", "CESMII Sensor", ua.VariantType.String)
   temp_sensor.add_variable('ns=2;s="C_TS1_SerialNumber"', "C_TS1 Serial Number", 12345678, ua.VariantType.UInt32)

   temp = temp_sensor.add_variable('ns=2;s="C_TS1_Temperature"', "C_TS1 Temperature", 20.0, ua.VariantType.Float)
   print("Furnace Temperature Nodeid {}".format(temp))

   now = datetime.datetime.now()
   Time = temp_sensor.add_variable('ns=2;s="C_TS1_Time"', "C_TS1 Time", now, ua.VariantType.DateTime)
   print("Furnace Time Nodeid {}".format(Time))
   #print("Time : "+str(Time.get_value()))


   furnace = objects.add_object('ns=2;s="C_CF1"', "Cesmii Furnace")
   print("Furnace Nodeid {}".format(furnace))

   furnace.add_variable('ns=2;s="C_CF1_ManfctrName"', "C_CF1 Manufacture Name", "CESMII Furnace", ua.VariantType.String)
   furnace.add_variable('ns=2;s="C_CF1_SerialNumber"', "C_CF1 Serial Number", 98765432, ua.VariantType.UInt32)

   state = furnace.add_variable('ns=2;s="C_CF1_DoorState"', "State of Furnace Door", False, ua.VariantType.Boolean)
   print("Furnace Door state Nodeid {}".format(state))

   state.set_writable()
   print("Door state Nodeid is {}".format(state.nodeid))

   temperature = 20.0

   """
       OPC-UA-Server Start
   """

   print("Start Server")
   server.start()
   print("Server Online at " + str(datetime.datetime.now()))
   print("Server Started at {}".format(endpoint_url))

   try:
       while True:
           #temperature += random.uniform(-1, 20)
           temperature = random.uniform(0, 100)
           temp.set_value(temperature)
           #print("Temperature : " + str(temp.get_value()))
           #print("State of Furnace Door: " + str(state.get_value()))

           TIME = datetime.datetime.now()
           Time.set_value(TIME)
           print("Time : "+str(Time.get_value()),"Temperature : "+str(temp.get_value()),"State of Door: " + str(state.get_value()))

           sleep(2)
   finally:
       server.stop()
       print("Server Offline")






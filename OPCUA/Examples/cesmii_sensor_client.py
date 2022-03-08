
#!/usr/bin/env python3

from opcua import Client
from time import sleep
import pandas as pd
import matplotlib.pyplot as plt


#client = Client("opc.tcp://192.168.1.6:62541")
client = Client("opc.tcp://localhost:62541")
client.connect()

print("Client Namespace Array : " + str(client.get_namespace_array()))

root_node = client.get_root_node()
print("Root Node ", root_node)

print("Children of root are: ", root_node.get_children())

#object_node = client.get_objects_node()
#print("Object Node: {}".format(object_node))

objects=client.get_objects_node()
print("Objects = {}".format(objects))
print(" Child 1 = {}".format(objects.get_children()[0]))
print(" Child 2 = {}".format(objects.get_children()[1]))
print(" Child 3 = {}".format(objects.get_children()[2]))

#print(objects.get_children()[1])

tempsens= objects.get_children()[1]
print("Temperature Senosr NodeID = " + str(tempsens))
print("Temperature Senors Attribute NodeID: {}".format(tempsens.get_children()))

for i in tempsens.get_children():
      i.get_value()
      print("Temperature Sensor Attribute value: {}".format((i.get_value())))


furnace= objects.get_children()[2]
print("Furnace NodeID ={}".format(furnace))
print("Furnace Attribte NodeID are " + str(furnace.get_children()))
for i in furnace.get_children():
      i.get_value()
      print("Furnace Attribute value " + str(i.get_value()))



state= furnace.get_children()[2]
print("Furnace state initial value " + str(state.get_value()))
print("Set State Value to True")
state.set_value(True)
print("New Furnace State value = {}".format(state.get_value()))


Temp = client.get_node('ns=2;s="C_TS1_Temperature"')
Temp.get_value()

print("Sensor Temperature browse name " + str(Temp.get_browse_name() ))
print("Sensor Temperature Value = {}".format(Temp.get_value()))




print("Collecting 5 temperature values to a dataframe")

df = pd.DataFrame(columns=['Temperature'])
i=0
while i < 5:
    Temp = client.get_node('ns=2;s="C_TS1_Temperature"')
    print (Temp.get_value())
    df = df.append({'Temperature': Temp.get_value()}, ignore_index=True)
    sleep(2)
    i += 1



#df.plot()
#plt.show()



#furnace.get_children()

door_state = client.get_node('ns=2;s="C_CF1_DoorState')
print(door_state)


furnace= objects.get_children()[2]
furnace.get_children()[2]
furnace.get_children()[2].get_value()


furnace.get_children()[2].set_value(True)
#print(furnace.get_children()[2].get_value())
print("Current Furnace State value = {}".format(furnace.get_children()[2].get_value()))

print("Set Furnace state to False")
furnace.get_children()[2].set_value(False)
furnace.get_children()[2].get_value()

print("Current Furnace State value = {}".format(furnace.get_children()[2].get_value()))


client.close_session()
print("Client Offline")



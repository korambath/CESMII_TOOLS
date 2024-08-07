
Requirements:

1. Availability of Python on your computer. You can use Anaconda to install Python for your architecture if you already don't have it.

https://www.anaconda.com/download

2. You must have an account with full Admin access to one of the CESMII SMIP (Smart Manufacturing Innovation Platform)

3. You should already have a GraphQL Authenticator created on your SMIP with full access permission

4. You should already create an information model with some attributes such as cpu_temperature, env_temperature, env_pressure, 
env_humidity env_altitude etc. 

5. This code assumes you are running this on RaspberryPI computer which serves as MQTT Publisher and you are using BME280 sensor.  If you just want
to simulate MQTT and don't want to use BME280 sensor, you can just crate random numbers  and run on any computer.

            sensor_data['cpu_temperature'] = cpu_temperature
            sensor_data['env_temperature'] = temperature
            sensor_data['env_humidity'] = humidity
            sensor_data['env_pressure'] = pressure
            sensor_data['env_altitude'] = altitude
 

Instructions to run the files

This code assumes you are transmitting five attributes shown above and you have access to the attribute ID of those variables from CESMII SMIP
You can always modify the number of parameters.

Before you are transmitting data  with GraphQL to the SMIP, you should replace everything marked 'REPLACE' with actual values from the platform. 
Get these values from the platform (name, authenticator, password_smip, role etc) from CESMII URL

For example, in credentials.py file

#### For MQTT (if you didn't setup your MQTT server with username/password then you don't need them)
broker = 'REPLACE'
port = 1883
topic = "REPLACE"
username = 'REPLACE'
password = 'REPLACE'

#### For CESMII SMIP

name= "REPLACE"
authenticator= "REPLACE"
password_smip= "REPLACE"
role= "REPLACE"
url= "https://<REPLACE>/graphql"



And in the transmit_bme280_to_cesmii.py 

write_attribute_id1 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id2 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id3 = "REPLACE"     #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id4 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id5 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model

Also you can look at 

https://github.com/cesmii/API/blob/main/Docs/mutations.md

https://github.com/cesmii/API/blob/main/Docs/queries.md


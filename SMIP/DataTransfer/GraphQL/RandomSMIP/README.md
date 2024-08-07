
Requirements:

1. Availability of Python on your computer. You can use Anaconda to install Python for your architecture if you already don't have it.

https://www.anaconda.com/download

2. You must have an account with full Admin access to one of the CESMII SMIP (Smart Manufacturing Innovation Platform)

3. You should already have a GraphQL Authenticator created on your SMIP with full access permission

4. You should already create an information model with some attributes such as temperature, pressure, humidity etc. 


Instructions to run the files

This code assumes you are transmitting three attributes (temperature, pressure, humidity). The values are randomly generated.
You can always modify the number of parameters.

Before you are transmitting data  with GraphQL to the SMIP, you should replace everything marked 'REPLACE' with actual values from the platform. 
Get these values from the platform (name, authenticator, password_smip, role etc) from CESMII URL

For example, in credentials.py file

name= "REPLACE"
authenticator= "REPLACE"
password_smip= "REPLACE"
role= "REPLACE"  ===> REPLACE this field as well with your group
url= "https://<urlname>/graphql" ===> Replace this field as well with your SMIP.

And in the transmit_random_to_cesmii.py 

write_attribute_id1 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id2 = "REPLACE"    #The Equipment Attribute ID to be updated in your SMIP model
write_attribute_id3 = "REPLACE"     #The Equipment Attribute ID to be updated in your SMIP model


Also you can look at 
https://github.com/cesmii/API/blob/main/Docs/mutations.md
https://github.com/cesmii/API/blob/main/Docs/queries.md


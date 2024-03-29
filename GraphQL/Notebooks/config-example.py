#!/usr/bin/env python
smip = {
    "verbose": 0,
    "authenticator": "myauthenticatorname",
    "password": "myauthenticatorspassword",
    "name": "myusername",
    "role": "myauthenticatorsrole",
    "url": "https://MYINSTANCE.cesmii.net/graphql",
    "bearer_token": "  ",
    "tagids": [1033, 3137],
    "startTimeOffset": 10000,
    "endTimeOffset": 0
}
excel = {
    "autoOpen": 1,
    "outputFile": "%temp%\output-$datetime.csv",
    "inputFile": "mutation_data.csv",
    "excelCommand": "start EXCEL.EXE",
    "note:": "on a mac use open -a 'path/Microsoft Excel.app'"
}

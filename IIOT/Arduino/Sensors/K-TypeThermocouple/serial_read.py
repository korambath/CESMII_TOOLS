#!/usr/bin/env python3
##############
## Script listens to serial port and writes contents into a file
##############
## requires pySerial to be installed
import time
import serial
from datetime import datetime

sensor = "MAX6675"
serial_port = '/dev/cu.usbmodem14401'
baud_rate = 9600 #In arduino, Serial.begin(baud_rate)
#baud_rate = 19200 #In arduino, Serial.begin(baud_rate)
#baud_rate = 74880 #In arduino, Serial.begin(baud_rate)
#baud_rate = 250000 #In arduino, Serial.begin(baud_rate)
write_to_file_path = "%s_LOG_%s.txt" % (str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")), sensor)

output_file = open(write_to_file_path, "w+")
ser = serial.Serial(serial_port, baud_rate)

# ser.readline().decode().strip()

timeData = []
while True:
    line = ser.readline().decode("utf-8")
    #print(time.time(),line)
    print(line.strip())
    #print(line)
    #timeData.append([time.time(),line])
    #timeData.append([datetime.now(),line])
    #output_file.write("{},{} \n".format(time.time(),line))
    #time.sleep(10)

output_file.close()

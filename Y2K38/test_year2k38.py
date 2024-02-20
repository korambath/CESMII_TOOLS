from datetime import datetime


print("Current UTC time = ", datetime.utcnow())
print("Current Local time = ", datetime.now())

epoch_seconds =  2147483647

print ("Last time that can be stored on 32 bit os ", datetime.fromtimestamp(epoch_seconds))
print ("Next Second on 64 bit OS ", datetime.fromtimestamp(epoch_seconds+1))

# 32 bit OS will display OverflowError: timestamp out of range for platform time_t

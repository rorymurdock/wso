"""Testing debugs"""
import sys
import wso
from basic_auth import Auth

UEM = wso.WSO(debug=True)

# Get device ID from serial
SERIAL = Auth().ask("Device serial")
DEVICE_ID = UEM.get_device(serial_number=SERIAL)['Id']['Value']

# Get user ID
USER = Auth().ask("New user")
USERNAME_ID = UEM.get_user(username=USER)['Users'][0]['Id']['Value']

# cChange users
if UEM.change_user(DEVICE_ID, USERNAME_ID):

    # Verify change completed
    new_user = UEM.get_device(serial_number=SERIAL)['UserName']

    if new_user == USER:
        print("Device %s's owner has been changed to %s" % (SERIAL, new_user))
        sys.exit()

print("Error changing owner on device %s" % SERIAL)

import wso

UEM = wso.WSO()

devices = UEM.get_all_devices()

for device in devices["Devices"]:
    print(device["DeviceFriendlyName"])

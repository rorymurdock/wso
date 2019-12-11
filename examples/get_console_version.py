import wso

UEM = wso.WSO()

VERSION = UEM.system_info()["ProductVersion"]
print("Console is running v%s" % VERSION)

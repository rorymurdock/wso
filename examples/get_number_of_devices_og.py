import wso

# Turn on debugging to see more info
UEM = wso.WSO(debug=False)

# OGS = UEM.get_all_ogs()

# for OG in OGS["OrganizationGroups"]:
#     print(OG)

devices = UEM.get_all_devices(pagesize=9999999)["Devices"]

print("OG,SerialNumber,ModelId,LastSeen")

for device in devices:
    print("%s,%s,%s,%s" %
          (device["LocationGroupId"]["Name"], device["SerialNumber"],
           device["ModelId"]["Name"], device["LastSeen"]))

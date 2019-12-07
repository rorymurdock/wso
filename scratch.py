from wso import WSO

wso = WSO()

# print(wso.system_info())

# print(wso.querystring(pagesize=100, OS="iOS"))

# print(wso.find_og("Playground", 40, 0))

# print(wso.remaining_api_calls())

# print(wso.get_product(1758))

# print(wso.get_product_device_state(1758, "compliant"))

# print(wso.get_product_assigned_groups(1758))

# print(wso.product_is_active(1758))

# print(wso.activate_product(1758))

# print(wso.get_all_devices(pagesize=1))

# print(wso.get_device_ip(17151522501902))

# print(wso.get_device_ip(device_id=1066))

# print(wso.get_device())
# print(wso.get_device(1066))
# print(wso.get_device(macaddress="4083DEE6A188"))
# print(wso.get_device(udid="49c4d83b8e0a383ffcbf2137c87e5752"))
# print(wso.get_device(serial_number="17151522501902"))

print(wso.get_device_extensive(1066))

# print(wso.bulk_limits())

# print(wso.device_counts())

print()


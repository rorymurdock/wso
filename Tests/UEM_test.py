"""Performs built tests for the UEM Module"""
from UEM import UEM
AW = UEM(debug=True)

def test_version():
    """Checks AW Version"""
    assert AW.system_info()['ProductVersion'] == '19.7.0.0'
    print(AW.system_info()['ProductVersion'])

# def test_get_og():
#     """Get AW OG"""
#     assert AW.get_og()["OrganizationGroups"][0]["Name"] == "pytest"
#     assert AW.get_og(name="pytest")["OrganizationGroups"][0] is None

# def test_get_device():
#     """Checks get_devices"""
#     assert AW.get_devices() == '{"Devices": [{}]}'

# def test_get_device_ip():
#     """Finds IP using all available search parameters"""
#     assert AW.get_device_ip() is None # No args
#     assert AW.get_device_ip(searchby="Macaddress", id=123456) is None # Non existing device
#     assert AW.get_device_ip(searchby="Udid", id=123456) is None # Non existing device
#     assert AW.get_device_ip(searchby="Serialnumber", id=123456) is None # Non existing device
#     assert AW.get_device_ip(searchby="ImeiNumber", id=123456) is None # Non existing device
#     assert AW.get_device_ip(searchby="BAD", id=123456) is None # Non existing device

#     #TODO Get existing device and then search the IP

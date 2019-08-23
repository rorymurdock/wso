"""Performs built tests for the UEM Module"""
import re
import json
import string
import random
import pytest
from reqREST import REST
from WSO.UEM import UEM
from WSO.configure import ConfigSetup

## Define CI Test items

# Root OG
ROOT_OG = "pytest"
ROOT_OG_ID = 4800

# NO_GROUP = 14
# Test product that already exists
TEST_PRODUCT_NAME = "CI Test Product"
TEST_PRODUCT_ID = 792
TEST_ACTIVE_PRODUCT_ID = 888

# Test group that already exists
TEST_GROUP_NAME = "PyTest CI Smart group"
TEST_GROUP_ID = 8686
ASSIGNED_GROUP = 9048

# Existing file ID
PRODUCT_ACTION_ITEM_ID = 622
PRODUCT_ACTION_TYPE_ID = 5
PRODUCT_PLATFORM_ID = 5

# Device serial and IP
TEST_DEVICE_SERIAL = 17142522504057
TEST_DEVICE_IP = '172.16.0.143'
TEST_DEVICE_ID = 14229

OG_TO_MOVE_TO = 'Staged'

# Random ID for the session
def random_chars(string_length=8):
    """Generate a random string of letters and digits """
    return ''.join(random.choice(
        string.ascii_uppercase + string.digits
        ) for i in range(string_length))

SESSION_ID = random_chars()

# Get AW version from API help page
##
with open('config/uem.json') as json_file:
    URL = json.load(json_file)['url']

# Create REST instance
vREST = REST(url=URL)

# At some stage the version file changed, try both
URLS = ['/api/help/local.json', '/api/system/help/localjson']

# Try the first URL
VERSION = vREST.get(URLS[0])

# If that 404's try the second URL
if VERSION.status_code == 404:
    VERSION = vREST.get(URLS[1])

# Delete the REST var for later use
del vREST

# If this 200 OKs
if VERSION.status_code == 200:
    # Get the text, parse is
    VERSIONS = json.loads(VERSION.text)
    VERSION = VERSIONS['apis'][0]['products'][0]

    # Regex it to remove AirWatch and VMWare Workspace ONE UEM strings
    # Leaving just the version number
    AIRWATCH_VERSION = re.match(
        r'(AirWatch|VMware Workspace ONE UEM);(.*)',
        VERSION,
        re.M|re.I
        ).group(2)

print('Test session ID: %s' % SESSION_ID)
print('Testing WSO UEM Version: %s' % VERSION)

AW = UEM(debug=True)

# Setup configs
def test_proxy_auth():
    """Sets up bad proxy for tests"""
    setup = ConfigSetup(overwrite=True, config_dir='config/proxy_config')
    assert setup.write_proxy_config('proxy.example.com', 80) is True
    assert setup.write_auth_config(
        'as114.awmdm.com',
        'YmFkdXNlcjpiYWRwYXNzd29yZA==',
        'tenantcode'
        ) is True

def test_bad_auth():
    """Sets up bad auth for tests"""
    setup = ConfigSetup(overwrite=True, config_dir='config/bad_config')
    assert setup.write_proxy_config() is True
    assert setup.write_auth_config('as138.awmdm.com', 'badauth', 'tenantcode') is True

# HTTP Code tests
def test_expected():
    """Test HTTP expected response"""
    assert AW.check_http_response(200, 200) is True

def test_unexpected():
    """Tests unexpected response is returns as False"""
    assert AW.check_http_response('unexpected') is False

def test_true_http():
    """Checks good responses are True"""
    demo_api = REST(url='postman-echo.com')
    for code in (200, 201, 204):
        assert AW.check_http_response(demo_api.get("/status/%i" % code).status_code) is True

def test_false_http():
    """Checks good responses are False"""
    demo_api = REST(url='postman-echo.com')
    for code in (400, 401, 403, 404, 422):
        assert AW.check_http_response(demo_api.get("/status/%i" % code).status_code) is False

# Test sub-functions
def test_json():
    """Tests converting str to json"""
    assert isinstance(AW.str_to_json('{"test":"ing"}'), dict) is True
    assert AW.str_to_json('{"test":"ing"}')['test'] == "ing"
    assert AW.str_to_json("string") is None

def test_append_url():
    """Tests appending arguments to URLs"""
    assert AW.append_url('a', {'b': 'c'}) == 'a?b=c'
    assert AW.append_url('a?b=c', {'d': 'e'}) == 'a?b=c&d=e'

def test_basic_url():
    """Tests basic URL GET"""
    response = AW.basic_url('/api/system/info')
    assert response[0]['ProductName'] == 'AirWatch Platform Service'
    assert isinstance(response[0], dict) is True
    assert response[1] == 200

    response = AW.basic_url('/api/404')
    assert response[0] is False
    assert response[1] == 404

    response = AW.basic_url('/api/help', expected_code=406)

    assert response[0] is None
    assert response[1] == 406


def test_bad_config_folder():
    """Tests bad config"""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        UEM('notexistantfolder')
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

def test_import_proxy():
    """Tests proxy settings"""
    # Used only to test proxy functions
    print(type(UEM(config_dir='config/proxy_config', debug=True).import_proxy()))
    assert isinstance(
        UEM(config_dir='config/proxy_config', debug=True).import_proxy(), dict
        ) is True

def test_bad_auth_apis():
    """Test bad auth failures"""
    bad_auth = UEM(config_dir='config/bad_config', debug=True)

    #TODO Update with new functions
    assert bad_auth.remaining_api_calls() is False
    assert bad_auth.system_info() is False
    assert bad_auth.get_og() is False
    assert bad_auth.get_group() is False
    assert bad_auth.get_name('product', 0) is False

# UEM API Tests
def test_version():
    """Checks AW Version"""
    assert AW.system_info()['ProductVersion'] == AIRWATCH_VERSION
    print(AW.system_info()['ProductVersion'])

def test_remaining_api_calls():
    """Checks remaining API calls"""
    assert isinstance(AW.remaining_api_calls(), int) is True

def test_get_og():
    """Get AW OG"""
    assert AW.get_og()["OrganizationGroups"][0]["Name"] == ROOT_OG
    assert AW.get_og(name="notexistantog")['OrganizationGroups'] == []

def test_get_product_name():
    """Tests resolving a product id to a name"""
    assert AW.get_product_name(TEST_PRODUCT_ID) == TEST_PRODUCT_NAME

def test_get_group_name():
    """Tests resolving a group id to a name"""
    assert AW.get_group_name(TEST_GROUP_ID) == TEST_GROUP_NAME

def test_get_group():
    """Tests getting group info"""
    assert isinstance(AW.get_group(TEST_GROUP_NAME), dict) is True
    assert isinstance(AW.get_group(groupid=TEST_GROUP_ID), dict) is True

# TODO
# def test_assign_products():

def test_product_is_active():
    """Test product activation state"""
    assert AW.product_is_active(TEST_ACTIVE_PRODUCT_ID) is True
    assert AW.product_is_active(TEST_PRODUCT_ID) is False

def test_activate_no_group_product():
    """Test activating a product with no assigned groups"""
    assert AW.activate_product(TEST_PRODUCT_ID) is False

def test_product():
    """Creates product, checks assignments, and then deactivates it"""
    # Create test product
    created_product_id = AW.create_product(
        'CI Test - %s' % SESSION_ID,
        'API CI Testing product, can be safely deleted', 5, 622, 5)

    assert isinstance(created_product_id, int) is True

    # Try to create product with name conflict
    assert AW.create_product(
        'CI Test - %s' % SESSION_ID,
        'API CI Testing product, can be deleted', 5, 622, 5) is False

    # Check product group assignements
    assert AW.get_product_assigned_groups(0) is False
    assert AW.get_product_assigned_groups(created_product_id) == []
    assert AW.activate_product(created_product_id) is False

    # Check product name
    response = AW.get_product_by_id(created_product_id)[0]
    assert response['Name'] == ('CI Test - %s' % SESSION_ID)
    assert response['Active'] is False

    # Assign group
    assert AW.assign_group_to_product(created_product_id, TEST_GROUP_ID) is True

    # Acivate Product
    assert AW.activate_product(created_product_id) is True
    assert AW.deactivate_product(created_product_id) is True
    assert AW.deactivate_product(created_product_id) is True
    assert AW.deactivate_product(created_product_id) is True

    # TODO assign group
    # TODO activate product

    # Delete newly created product
    assert AW.delete_product(created_product_id) is True
    assert AW.delete_product(created_product_id) is False
    assert AW.delete_product(TEST_ACTIVE_PRODUCT_ID) is False

def test_get_all_devices():
    """Tests getting a list of all devices"""
    # Possible improvement: Check for device details, serials etc
    response = AW.get_all_devices()
    assert isinstance(response, dict) is True
    assert response['Devices'] != []

def test_get_device_ip():
    """Tests getting a device IP"""
    assert AW.get_device_ip(TEST_DEVICE_SERIAL) == TEST_DEVICE_IP
    assert AW.get_device_ip('11111') is False

def test_get_device():
    """Test getting device info"""
    device = AW.get_device(TEST_DEVICE_SERIAL)
    assert device['Id']['Value'] == TEST_DEVICE_ID

def test_get_device_extensive():
    """Test getting extensive device info"""
    device_id = AW.get_device(TEST_DEVICE_SERIAL)['Id']['Value']
    response = AW.get_device_extensive(device_id)['Devices'][0]

    assert response['DeviceId'] == TEST_DEVICE_ID
    assert response['DeviceUuid'] == 'a9f524fc-f9c8-4f64-9992-140944b16abe'
    assert response['Udid'] == '433f4189881517307f0431ac622558be'
    assert response['SerialNumber'] == str(TEST_DEVICE_SERIAL)
    assert response['DeviceFriendlyName'] == 'pytest Android_TC51_null 4057'
    assert response['UserName'] == 'pytest_enrol'
    assert response['LastSeen'] == '2019-07-03T22:14:26.290'
    assert response['EnrollmentDate'] == '2019-06-19T11:42:11.580'
    assert response['Compliant'] is True
    assert response['AssetNumber'] == '433f4189881517307f0431ac622558be'
    assert response['EnrollmentStatus'] == 'Enrolled'
    assert response['Products'][0]['ProductId'] == 846
    assert response['Products'][0]['Name'] == 'Product Set 1'
    assert response['Products'][0]['Status'] == 'Compliant'
    assert response['SmartGroups'][0]['SmartGroupId'] == 1155
    assert response['SmartGroups'][0]['SmartGroupUuid'] == '14a44cb1-5b15-e711-80c4-0025b5010089'
    assert response['SmartGroups'][0]['Name'] == 'All Devices'
    assert response['CustomAttributes'][0]['Name'] == 'identity.deviceModel'
    assert response['CustomAttributes'][0]['Value'] == 'TC51'
    assert response['CustomAttributes'][0]['ApplicationGroup'] == 'com.airwatch.androidagent.identity.xml'



def test_format_group_payload_devices():
    """Test formatting a group payload"""
    payload = {'Name': 'Test',
               'CriteriaType': 'UserDevice',
               'DeviceAdditions': []
               }

    devices = [123, 456, TEST_DEVICE_SERIAL, 9999]
    group_name = 'Test'

    # Test no device payload
    assert isinstance(AW.format_group_payload_devices(group_name, [devices[0], devices[1]]), dict) is True

    # Test 1 device payload
    payload['DeviceAdditions'].append({'Id': 14229, 'Name': 'pytest Android_TC51_null 4057'})
    assert AW.format_group_payload_devices(group_name, devices) == payload

def test_format_group_payload_ogs():
    """Test formatting a group payload"""
    payload = {'Name': 'Test',
               'CriteriaType': 'All',
               'OrganizationGroups': []
               }

    ogs = [123, 456, ROOT_OG, 'AAAA']
    group_name = 'Test'


    # Test no og payload
    assert isinstance(AW.format_group_payload_ogs(group_name, [ogs[0], ogs[1]]), dict) is True

    # Test 1 og payload
    payload['OrganizationGroups'].append({'Id': 4800, 'Name': 'pytest', 'Uuid': 'ffa89488-34cd-44c2-8cc5-2d7d3e02ef5e'})
    assert AW.format_group_payload_ogs(group_name, ogs) == payload


def test_create_delete_group_from_og():
    """Creates a group based on a list of OGs, deletes it"""

    group = AW.create_group_from_ogs('CI Test - %s' % SESSION_ID, [ROOT_OG])
    response = AW.create_group_from_ogs('CI Test - %s' % SESSION_ID, [ROOT_OG]) is False
    assert response is False
    assert group.success is True

    assert AW.delete_group(group.id) is True
    assert AW.delete_group(0) is False

    # Try to delete a group that is assigned
    assert AW.delete_group(ASSIGNED_GROUP) is False

def test_create_group_from_devices():
    """Creates a group based on a list of devices, deletes it"""

    group = AW.create_group_from_devices('CI Test - %s' % SESSION_ID, [TEST_DEVICE_SERIAL])
    assert group.success is True

    assert AW.delete_group(group.id) is True

def test_remove_group_from_product():
    """Test removing group from a product"""
    # Remove all assigned groups
    AW.remove_all_groups_from_product(TEST_PRODUCT_ID)
    assert AW.check_no_group_assignments(TEST_PRODUCT_ID) is True

    # Assign 1 group to product
    assert AW.assign_group_to_product(TEST_PRODUCT_ID, 8686) is True
    assert AW.check_no_group_assignments(TEST_PRODUCT_ID) is False

    # Remove the 1 assigned group and make sure it's not longer assigned
    assert AW.remove_group_from_product(TEST_PRODUCT_ID, TEST_GROUP_ID)
    assert AW.check_no_group_assignments(TEST_PRODUCT_ID) is True

    # Remove invalid IDs
    assert AW.remove_group_from_product(TEST_PRODUCT_ID, 0) is False
    assert AW.remove_group_from_product(0, TEST_GROUP_ID) is False


def test_assign_group_to_product():
    """Tests assigning groups to a product"""
    # Remove all groups from the product first
    AW.remove_all_groups_from_product(TEST_PRODUCT_ID)

    assert AW.assign_group_to_product(TEST_PRODUCT_ID, TEST_GROUP_ID) is True
    # Should still return True if already assigned
    assert AW.assign_group_to_product(TEST_PRODUCT_ID, TEST_GROUP_ID) is True

    # Invalid group ID
    assert AW.assign_group_to_product(TEST_PRODUCT_ID, 0) is False

    # Invalid product ID
    assert AW.assign_group_to_product(0, TEST_GROUP_ID) is False

def test_activate_product():
    """Tests activating a product"""
    assert AW.activate_product(TEST_PRODUCT_ID) is True

def test_deactivate_product():
    """Tests deactivating a product"""
    assert AW.deactivate_product(TEST_PRODUCT_ID) is True

def test_remove_groups_from_products():
    """Test removing all groups from a product"""
    # Remove the groups just assigned
    assert AW.remove_all_groups_from_product(TEST_PRODUCT_ID) is True
    assert AW.check_no_group_assignments(TEST_PRODUCT_ID) is True

    # Test bad product ID
    assert AW.remove_all_groups_from_product(0) is False

def test_tag_full():
    """Test creating a tag, assign, unassign, and delete"""
    new_tag = AW.create_tag('CI Test - %s' % SESSION_ID)
    assert isinstance(new_tag, int)
    # Create tag again to get the same int
    duplicate_tag = AW.create_tag('CI Test - %s' % SESSION_ID)
    assert isinstance(duplicate_tag, int)
    assert duplicate_tag == new_tag
    tag_id = AW.get_tag('CI Test - %s' % SESSION_ID)[0]['Id']['Value']
    assert AW.add_tag(tag_id, [TEST_DEVICE_ID])
    assert AW.get_tagged_devices(tag_id)[0]['DeviceId'] == TEST_DEVICE_ID
    assert AW.remove_tag(tag_id, [TEST_DEVICE_ID]) is True
    assert AW.delete_tag(tag_id) is True

def test_tag_errors():
    assert AW.x_tag('badaction', 999, [0, 0]) is False

def test_change_og():
    change_og_id = AW.get_og(name=OG_TO_MOVE_TO)['OrganizationGroups'][0]['Id']

    # Move device to the root OG to start with
    AW.change_og(TEST_DEVICE_SERIAL, ROOT_OG_ID)
    assert AW.get_device(TEST_DEVICE_SERIAL)['LocationGroupName'] == ROOT_OG

    # Move device to the Staging OG
    AW.change_og(TEST_DEVICE_SERIAL, change_og_id)
    assert AW.get_device(TEST_DEVICE_SERIAL)['LocationGroupName'] == OG_TO_MOVE_TO

    # Move device back to the root OG to finish up
    AW.change_og(TEST_DEVICE_SERIAL, ROOT_OG_ID)
    assert AW.get_device(TEST_DEVICE_SERIAL)['LocationGroupName'] == ROOT_OG

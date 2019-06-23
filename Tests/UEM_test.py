"""Performs built tests for the UEM Module"""
import string
import random
import pytest
from REST import REST
from UEM import UEM
from setup import ConfigSetup

## Define CI Test items
# Expected AW version
AIRWATCH_VERSION = '19.7.0.0'

# Root OG
ROOT_OG = "pytest"

# NO_GROUP = 14
# Test product that already exists
TEST_PRODUCT_NAME = "CI Test Product"
TEST_PRODUCT_ID = 792

# Test group that already exists
TEST_GROUP_NAME = "PyTest CI Smart group"
TEST_GROUP_ID = 8686

# Existing file ID
PRODUCT_ACTION_ITEM_ID = 622
PRODUCT_ACTION_TYPE_ID = 5
PRODUCT_PLATFORM_ID = 5

# Device serial and IP
TEST_DEVICE_SERIAL = 17142522504057
TEST_DEVICE_IP = '172.16.0.141'

AW = UEM(debug=True)

def random_chars(string_length=8):
    """Generate a random string of letters and digits """
    return ''.join(random.choice(
        string.ascii_uppercase + string.digits
        ) for i in range(string_length))

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

    assert bad_auth.remaining_api_calls() is False
    assert bad_auth.system_info() is False
    assert bad_auth.get_og() is False
    assert bad_auth.get_group() is False
    assert bad_auth.get_name('product', 0) is False
    assert bad_auth.activate_product(0, True) is False
    assert bad_auth.delete_product(0)  is False

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

# def test_assign_products():

def test_product():
    """Creates product, checks assignments, and then deactivates it"""
    # Create test product
    product_random = random_chars()
    created_product_id = AW.create_product(
        'CI Test - %s' % product_random,
        'API CI Testing product, can be safely deleted', 5, 622, 5)

    assert isinstance(created_product_id, int) is True

    # Try to create product with name conflict
    assert AW.create_product(
        'CI Test - %s' % product_random,
        'API CI Testing product, can be deleted', 5, 622, 5) is False

    # Check product group assignements
    assert AW.get_product_assigned_groups(created_product_id) == []
    assert AW.activate_product(created_product_id) is False

    # Check product name
    response = AW.get_product(created_product_id)[0]
    assert response['Name'] == ('CI Test - %s' % product_random)
    assert response['Active'] is False

    # TODO assign group
    # TODO activate product

    # Delete newly created product
    assert AW.delete_product(created_product_id) is True
    assert AW.delete_product(created_product_id) is False

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

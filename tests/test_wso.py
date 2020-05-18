"""Automated testing for WSO"""
import re
import json
import argparse
import random
import string
import requests
import pytest
from reqrest import REST
from basic_auth import Auth
from wso.configure import Config
from wso.wso import WSO

# Define CI Test items

# Root OG
ROOT_OG = "pytest"
ROOT_OG_ID = 4800

# NO_GROUP = 14
# Test product that already exists
TEST_PRODUCT_NAME = "CI Test Product"
TEST_PRODUCT_ID = 792
TEST_ACTIVE_PRODUCT_ID = 888
TEST_ASSIGNED_PRODUCT = 930
TEST_AUTODEPLOY_PRODUCT = 1024

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
TEST_DEVICE_FRIENDLY_NAME = 'pytest Android_TC51_null 4057'
TEST_DEVICE_LAST_SEEN = '07-03-2019 22:14:26.290'

OG_TO_MOVE_TO = 'Staged'


# Random int / str generators
def random_string(string_length=15):
    """Generate a random string of x length"""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))


def random_number():
    """Generate a random number of fixed length (4)"""
    return random.randint(0, 9999)


# Random ID for the session
def random_chars(string_length=8):
    """Generate a random string of letters and digits """
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for i in range(string_length))


# Create some random values to use for testing
RANDOM_URL = "cn%i.awmdmtest.com" % random_number()
RANDOM_USERNAME = random_string(8)
RANDOM_PASSWORD = random_string()
RANDOM_TENANTCODE = random_string()
RANDOM_PROXYSERVER = random_string(8)
RANDOM_PROXYPORT = random_number()

SESSION_ID = random_chars()

print('Test session ID: %s' % SESSION_ID)

# Create globals
UEM = WSO()
CONFIG = Auth().read_config("uem.json")
CONFIG_DIR = "config-wso-tests"

# Init package
AUTH = Auth(config_dir=CONFIG_DIR)

# Tests


def test_bad_config_folder():
    """Tests bad config"""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        WSO('notexistantfolder')
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 2

    # TODO Stage and test stdin


def test_good_config_folder():
    """Tests good config"""

    assert isinstance(WSO('config').system_info(), dict)


def test_create_headers():
    """Test assembling the header structure"""
    # Test v1
    headers = UEM.create_headers(version=1)

    assert headers["Accept"] == "application/json;version=1"
    assert headers["Authorization"] == CONFIG['authorization']
    assert headers["Content-Type"] == 'application/json'
    assert headers["aw-tenant-code"] == CONFIG['aw-tenant-code']

    # Try again with v2
    headers = UEM.create_headers()

    assert headers["Accept"] == "application/json;version=2"
    assert headers["Authorization"] == CONFIG['authorization']
    assert headers["Content-Type"] == 'application/json'
    assert headers["aw-tenant-code"] == CONFIG['aw-tenant-code']


def test_import_proxy():
    """Test mocking the arguments and running them through main()"""

    filename = 'wso_args_proxy.json'

    # Create mock
    args = argparse.Namespace(url=RANDOM_URL,
                              username=RANDOM_USERNAME,
                              password=RANDOM_PASSWORD,
                              tenantcode=RANDOM_TENANTCODE,
                              proxyserver=RANDOM_PROXYSERVER,
                              proxyport=RANDOM_PROXYPORT,
                              directory=CONFIG_DIR)

    result = Config(config_dir=CONFIG_DIR, output=filename).main(args)

    assert result is True

    assert AUTH.check_file_exists(filename) is True

    assert AUTH.verify_config(filename, 'authorization',
                              AUTH.encode(RANDOM_USERNAME,
                                          RANDOM_PASSWORD)) is True
    assert AUTH.verify_config(filename, 'url', RANDOM_URL) is True
    assert AUTH.verify_config(filename, 'aw-tenant-code',
                              RANDOM_TENANTCODE) is True
    assert AUTH.verify_config(filename, 'proxyserver',
                              RANDOM_PROXYSERVER) is True
    assert AUTH.verify_config(filename, 'proxyport', RANDOM_PROXYPORT) is True

    proxy = WSO(config_dir=CONFIG_DIR,
                config_file="wso_args_proxy.json").import_proxy()

    expected_proxy = {}
    expected_proxy["http"] = "%s:%s" % (RANDOM_PROXYSERVER, RANDOM_PROXYPORT)
    expected_proxy["https"] = "%s:%s" % (RANDOM_PROXYSERVER, RANDOM_PROXYPORT)
    assert proxy == expected_proxy


def test_import_noproxy():
    """Test importing the proxy settings"""
    proxy = UEM.import_proxy()
    assert proxy is None


def test_system_info():
    """Test system_info API"""
    info = UEM.system_info()
    assert isinstance(info, dict) is True

    # Get the API version
    version = REST(url=CONFIG['url']).get("/api/system/help/localjson")
    version = json.loads(version.text)

    # Extract the version code
    version = re.search(r'(\d{1,2}.\d{1,2}.\d{1,2}.\d{1,2})',
                        version["apis"][0]['products'][0]).group(1)

    assert info['ProductVersion'] == version


def test_expected():
    """Test HTTP expected response"""
    response = requests.models.Response()
    response.status_code = 200

    assert UEM.check_http_response(response, 200) is True


def test_unexpected():
    """Tests unexpected response is returns as False"""
    response = requests.models.Response()
    response.status_code = 'unexpected'

    assert UEM.check_http_response(response) is False


def test_true_http():
    """Checks good responses are True"""
    demo_api = REST(url='postman-echo.com')
    for code in (200, 201, 204):
        assert UEM.check_http_response(demo_api.get(
            "/status/%i" % code)) is True


def test_false_http():
    """Checks good responses are False"""
    demo_api = REST(url='postman-echo.com')
    for code in (400, 401, 403, 404, 406, 422, 500):
        assert UEM.check_http_response(demo_api.get(
            "/status/%i" % code)) is False


def test_str_to_json():
    """Test converting a str to json"""
    # Test large string
    ninek_str = "x" * 9000
    test_large_json = {}
    test_large_json['XL_test'] = ninek_str
    test_large_str = json.dumps(test_large_json)

    assert UEM.str_to_json(test_large_str) == test_large_json

    # Test large string
    oneh_str = "y" * 100
    test_small_json = {}
    test_small_json['SM_Test'] = oneh_str
    test_small_str = json.dumps(test_small_json)

    assert UEM.str_to_json(test_small_str) == test_small_json

    # Test non json input

    assert UEM.str_to_json("str no json") is None


def test_querystring():
    """Test submitting multiple params to querystring"""

    # Create some typical parameters requested
    user = random_string
    model = None
    platform = None
    lastseen = None
    ownership = None
    lgid = None
    compliantstatus = None
    seensince = None
    orderby = None
    sortorder = None
    pagesize = random_number()
    page = 0

    # Filter Q's
    querystring = UEM.querystring(user=user,
                                  model=model,
                                  platform=platform,
                                  lastseen=lastseen,
                                  ownership=ownership,
                                  lgid=lgid,
                                  compliantstatus=compliantstatus,
                                  seensince=seensince,
                                  orderby=orderby,
                                  sortorder=sortorder,
                                  pagesize=pagesize,
                                  page=page)

    # Check only the vaid params weren't filtered
    assert len(querystring) == 3
    assert querystring["page"] == page
    assert querystring["pagesize"] == pagesize
    assert querystring["user"] == user


def test_simple_get():
    """Test simple_get fucntion"""
    filename = 'postman-config.json'

    # Create mock
    args = argparse.Namespace(url="postman-echo.com",
                              username=RANDOM_USERNAME,
                              password=RANDOM_PASSWORD,
                              tenantcode=RANDOM_TENANTCODE,
                              proxyserver=None,
                              proxyport=None,
                              directory=CONFIG_DIR)

    Config(config_dir=CONFIG_DIR, output=filename).main(args)

    wso = WSO(config_dir=CONFIG_DIR, config_file=filename)

    # Check v2 default
    response = wso.simple_get("/headers/")
    assert response["headers"]["accept"] == "application/json;version=2"
    assert response["headers"]["authorization"] == AUTH.encode(
        RANDOM_USERNAME, RANDOM_PASSWORD)
    assert response["headers"]["aw-tenant-code"] == RANDOM_TENANTCODE

    # Check v1
    response = wso.simple_get("/headers/", version=1)
    assert response["headers"]["accept"] == "application/json;version=1"
    assert response["headers"]["authorization"] == AUTH.encode(
        RANDOM_USERNAME, RANDOM_PASSWORD)
    assert response["headers"]["aw-tenant-code"] == RANDOM_TENANTCODE

    # Test querystring
    querystring = {}
    querystring[RANDOM_USERNAME] = RANDOM_TENANTCODE

    response = wso.simple_get("/get/", querystring=querystring, version=1)
    assert response["args"][RANDOM_USERNAME] == RANDOM_TENANTCODE

    # Test 204 returns None
    response = wso.simple_get("/status/204", version=1)
    assert response is None

    # Test over 9k size
    querystring["9k"] = "z" * 9000
    response = wso.simple_get("/status/204",
                              querystring=querystring,
                              version=1)


def test_get_product_name():
    """Tests resolving a product id to a name"""
    assert UEM.get_product_name(TEST_PRODUCT_ID) == TEST_PRODUCT_NAME
    assert UEM.get_product_name("BADPRODUCT") is False


def test_get_group_name():
    """Tests resolving a group id to a name"""
    assert UEM.get_group_name(TEST_GROUP_ID) == TEST_GROUP_NAME
    assert UEM.get_group_name("BADGROUP") is False


def test_filter_locals():
    """Test filtering self out of local vars"""

    _local = {}
    _local["path"] = "/api/system/info"
    _local["self"] = "3a863bfd0"
    _local["version"] = 1

    org_len = len(_local)

    _local_filtered = UEM.filter_locals(_local)

    assert len(_local_filtered) == org_len - 1
    assert "self" not in _local_filtered

    _local_filtered = UEM.filter_locals(_local)
    assert len(_local_filtered) == org_len - 1


def test_remaining_api_calls():
    """Checks remaining API calls"""
    assert isinstance(UEM.remaining_api_calls(), int) is True


def test_find_og():
    """Test finding an OG"""

    org_group = UEM.find_og(pagesize=1)
    assert org_group["OrganizationGroups"][0]["GroupId"] == "pytest"

    staged = UEM.find_og("Staged", pagesize=1)
    assert staged["OrganizationGroups"][0]["Id"] == 4801


def test_get_og():
    """Test getting a specific OG"""
    og_id = ROOT_OG_ID

    org_group = UEM.get_og(og_id)

    assert org_group["GroupId"] == ROOT_OG
    assert org_group["Name"] == ROOT_OG


def test_get_all_ogs():
    """Test getting all of the OGs"""

    ogs = UEM.get_all_ogs()

    assert ogs["TotalResults"] == 2

    assert ogs["OrganizationGroups"][0]["Name"] == ROOT_OG
    assert ogs["OrganizationGroups"][0]["Id"] == ROOT_OG_ID
    assert ogs["OrganizationGroups"][1]["Name"] == "Staged"
    assert ogs["OrganizationGroups"][1]["Id"] == 4801


def test_bulk_limits():
    """Get the console bulk limits"""

    limits = UEM.bulk_limits()

    assert limits["DeleteDevice"] == 3000
    assert limits["EnterpriseWipe"] == 10
    assert limits["GPS"] == 500
    assert limits["LockDevice"] == 3000
    assert limits["SendMessage"] == 3000


def test_device_counts():
    """Test the device counts from the console"""

    counts = UEM.device_counts()

    assert counts["EnrollmentStatus"]["Enrolled"] == 1
    assert counts["EnrollmentStatus"]["Registered"] == 0
    assert counts["EnrollmentStatus"]["Unenrolled"] == 0
    assert counts["Ownership"]["Undefined"] == 1
    assert counts["Platforms"]["Android"] == 1
    assert counts["Security"]["Compromised"] == 0
    assert counts["Security"]["NoPasscode"] == 0
    assert counts["Security"]["NotEncrypted"] == 0
    assert counts["TotalDevices"] == 1


def test_get_group():
    """Tests getting group info"""
    group = UEM.get_group(group_id=TEST_GROUP_ID)

    assert group["Name"] == "PyTest CI Smart group"
    assert group["Devices"] == 1


def test_find_group():
    """Test finding a group"""
    group = UEM.find_group(name=TEST_GROUP_NAME)

    assert group["SmartGroups"][0]["SmartGroupID"] == 8686
    assert group["SmartGroups"][0]["Devices"] == 1


def test_create_product():
    """Test creating a product"""

    # Create a test product
    created_product_id = UEM.create_product(
        'CI Test - %s' % SESSION_ID,
        'API CI Testing product, can be safely deleted', 5, 622, 5)

    # Create a test product by specify the root OG
    created_product_id_x = UEM.create_product(
        'CI Test - %s X' % SESSION_ID,
        'API CI Testing product, can be safely deleted', 5, 622, 5, ROOT_OG_ID)

    assert isinstance(created_product_id, int) is True

    assert isinstance(created_product_id_x, int) is True

    assert UEM.delete_product(created_product_id_x) is True


def test_find_product():
    """Test finding a product by name"""
    product = UEM.find_product("CI Test - %s" % SESSION_ID)

    assert product["Products"][0]["Name"] == "CI Test - %s" % SESSION_ID


def test_get_product():
    """Test getting a product"""
    product = UEM.get_product(TEST_PRODUCT_ID)

    assert product["Name"] == TEST_PRODUCT_NAME


def test_get_product_device_state():
    """Test getting device state for products"""
    # Test bad ID
    assert UEM.get_product_device_state(0, 'assigned') is False

    # Test bad state
    assert UEM.get_product_device_state(TEST_PRODUCT_ID, 'badassigned') is None

    # Test bad everything
    assert UEM.get_product_device_state(0, 'badassigned') is None

    # Test inactive product
    assert UEM.get_product_device_state(
        TEST_PRODUCT_ID, 'assigned', pagesize=10) is None

    # Test active product
    devices = {}
    devices['Devices'] = []

    device = {}
    device['DeviceId'] = TEST_DEVICE_ID
    device['Name'] = TEST_DEVICE_FRIENDLY_NAME
    device['LastJobStatus'] = 'NoJobs'
    device['LastSeen'] = TEST_DEVICE_LAST_SEEN

    devices['Devices'].append(device)
    devices['Page'] = 0
    devices['PageSize'] = 10
    devices['Total'] = 0  # Bug, returns 0: WSO ticket #20115390404

    assert UEM.get_product_device_state(TEST_ASSIGNED_PRODUCT,
                                        'assigned',
                                        pagesize=10) == devices


def test_get_product_assigned_groups():
    """Test getting assigned groups for products"""
    product_id_no_group = UEM.find_product(
        "CI Test - %s" % SESSION_ID)["Products"][0]["ID"]["Value"]
    # Check product group assignements
    assert UEM.get_product_assigned_groups(0) is False
    assert UEM.get_product_assigned_groups(product_id_no_group) == []

    assert UEM.get_product_assigned_groups(TEST_ASSIGNED_PRODUCT) == [{
        'SmartGroupId':
        9048,
        'Name':
        'CI Assigned Group'
    }]


def test_product_is_active():
    """Test product activation state"""
    assert UEM.product_is_active(TEST_ACTIVE_PRODUCT_ID) is True
    assert UEM.product_is_active(TEST_PRODUCT_ID) is False


def test_activate_no_group_product():
    """Test activating a product with no assigned groups"""
    assert UEM.activate_product(TEST_PRODUCT_ID) is False


def test_assign_group_to_product():
    """Tests assigning groups to a product"""
    # Remove all groups from the product first
    UEM.remove_all_groups_from_product(TEST_PRODUCT_ID)

    assert UEM.assign_group_to_product(TEST_PRODUCT_ID, TEST_GROUP_ID) is True

    # Test reprocessing
    UEM.remove_group_from_product(TEST_ACTIVE_PRODUCT_ID, TEST_GROUP_ID)
    assert UEM.assign_group_to_product(TEST_ACTIVE_PRODUCT_ID,
                                       TEST_GROUP_ID) is True

    # Should still return True if already assigned
    assert UEM.assign_group_to_product(TEST_PRODUCT_ID, TEST_GROUP_ID) is True

    # Invalid group ID
    assert UEM.assign_group_to_product(TEST_PRODUCT_ID, 0) is False

    # Invalid product ID
    assert UEM.assign_group_to_product(0, TEST_GROUP_ID) is False


def test_activate_product():
    """Tests activating a product"""
    assert UEM.activate_product(TEST_PRODUCT_ID) is True
    assert UEM.activate_product(TEST_PRODUCT_ID) is True
    assert UEM.activate_product(TEST_AUTODEPLOY_PRODUCT) is True


def test_deactivate_product():
    """Tests deactivating a product"""
    assert UEM.deactivate_product(TEST_PRODUCT_ID) is True


def test_remove_groups_from_products():
    """Test removing all groups from a product"""
    # Remove the groups just assigned
    assert UEM.remove_all_groups_from_product(TEST_PRODUCT_ID) is True
    assert UEM.check_no_group_assignments(TEST_PRODUCT_ID) is True

    # Test bad product ID
    assert UEM.remove_all_groups_from_product(0) is False


def test_check_no_group_assignments():
    """Check product group assignments"""
    assert UEM.check_no_group_assignments(TEST_PRODUCT_ID) is True
    assert UEM.check_no_group_assignments(TEST_ACTIVE_PRODUCT_ID) is False


def test_delete_product():
    """Test deleting a product"""
    created_product_id = UEM.find_product(
        "CI Test - %s" % SESSION_ID)["Products"][0]["ID"]["Value"]

    assert UEM.delete_product(created_product_id) is True
    assert UEM.delete_product(created_product_id) is False
    assert UEM.delete_product(TEST_ACTIVE_PRODUCT_ID) is False


def test_get_device():
    """Test getting device info"""
    device = UEM.get_device(serial_number=TEST_DEVICE_SERIAL)
    assert device['Id']['Value'] == TEST_DEVICE_ID
    assert UEM.get_device() is False


def test_get_all_devices():
    """Test getting all device info"""
    devices = UEM.get_all_devices()
    assert devices["Devices"][0]['Id']['Value'] == TEST_DEVICE_ID


def test_get_device_ip():
    """Tests getting a device IP"""
    assert UEM.get_device_ip(
        serial_number=TEST_DEVICE_SERIAL) == TEST_DEVICE_IP
    assert UEM.get_device_ip(device_id=TEST_DEVICE_ID) == TEST_DEVICE_IP
    assert UEM.get_device_ip('11111') is False
    assert UEM.get_device_ip() is False


def test_get_device_extensive():
    """Test getting extensive device info"""
    device_id = UEM.get_device(serial_number=TEST_DEVICE_SERIAL)['Id']['Value']
    response = UEM.get_device_extensive(device_id=device_id)['Devices'][0]

    assert response['DeviceId'] == TEST_DEVICE_ID
    assert response['DeviceUuid'] == 'a9f524fc-f9c8-4f64-9992-140944b16abe'
    assert response['Udid'] == '433f4189881517307f0431ac622558be'
    assert response['SerialNumber'] == str(TEST_DEVICE_SERIAL)
    assert response['DeviceFriendlyName'] == TEST_DEVICE_FRIENDLY_NAME
    assert response['UserName'] == 'pytest_enrol'
    assert response['LastSeen'] == '2019-07-03T22:14:26.290'
    assert response['EnrollmentDate'] == '2019-06-19T11:42:11.580'
    assert response['Compliant'] is True
    assert response['AssetNumber'] == '433f4189881517307f0431ac622558be'
    assert response['EnrollmentStatus'] == 'Enrolled'
    assert response['SmartGroups'][0]['SmartGroupId'] == 1155
    assert response['SmartGroups'][0][
        'SmartGroupUuid'] == '14a44cb1-5b15-e711-80c4-0025b5010089'
    assert response['SmartGroups'][0]['Name'] == 'All Devices'
    assert response['CustomAttributes'][0]['Name'] == 'identity.deviceModel'
    assert response['CustomAttributes'][0]['Value'] == 'TC51'
    assert response['CustomAttributes'][0][
        'ApplicationGroup'] == 'com.airwatch.androidagent.identity.xml'

    assert UEM.get_device_extensive() is False


def test_create_group_from_devices():
    """Creates a group based on a list of devices, deletes it"""

    group = UEM.create_group_from_devices('CI Test - %s' % SESSION_ID,
                                          [TEST_DEVICE_SERIAL, 12345])
    assert isinstance(group, int)

    assert UEM.delete_group(group) is True

    assert UEM.delete_group(0) is False

    assert UEM.create_group_from_devices('CI Test - %s' % SESSION_ID + "X",
                                         []) is False


def test_create_group_from_devices_bulk():
    """Creates a group based on a bulk list of devices, deletes it"""

    bulk_device_list = []
    bulk_device_list.append(TEST_DEVICE_SERIAL)

    for i in range(100):
        bulk_device_list.append(i)

    bulk_device_list.append(TEST_DEVICE_SERIAL)

    group = UEM.create_group_from_devices('CI Test - %s' % SESSION_ID,
                                          bulk_device_list)
    assert isinstance(group, int)

    assert UEM.delete_group(group) is True

    assert UEM.delete_group(0) is False

    assert UEM.create_group_from_devices('CI Test - %s' % SESSION_ID + "X",
                                         []) is False


def test_create_delete_group_from_og():
    """Creates a group based on a list of OGs, deletes it"""

    group = UEM.create_group_from_ogs('CI Test - %s' % SESSION_ID,
                                      [ROOT_OG, "ABCD"])
    assert isinstance(group, int)

    response = UEM.create_group_from_ogs('CI Test - %s' % SESSION_ID,
                                         [ROOT_OG])
    assert response is False

    assert UEM.create_group_from_ogs('CI Test - %s' % SESSION_ID + "X",
                                     []) is False

    assert UEM.delete_group(group) is True
    assert UEM.delete_group(0) is False

    # Try to delete a group that is assigned
    assert UEM.delete_group(ASSIGNED_GROUP) is False


def test_tag_full():
    """Test creating a tag, assign, unassign, and delete"""
    new_tag = UEM.create_tag('CI Test - %s' % SESSION_ID)
    assert isinstance(new_tag, int)
    # Create tag again to get the same int
    duplicate_tag = UEM.create_tag('CI Test - %s' % SESSION_ID)
    assert isinstance(duplicate_tag, int)
    assert duplicate_tag == new_tag
    tag_id = UEM.find_tag('CI Test - %s' % SESSION_ID)[0]['Id']['Value']
    assert UEM.add_tag(tag_id, [TEST_DEVICE_ID])
    assert UEM.get_tagged_devices(tag_id)[0]['DeviceId'] == TEST_DEVICE_ID
    assert UEM.remove_tag(tag_id, [TEST_DEVICE_ID]) is True
    assert UEM.delete_tag(tag_id) is True


def test_tag_errors():
    """Test a bad tag action"""
    assert UEM.x_tag('badaction', 999, [0, 0]) is False


def test_get_printer():
    """Test the get printer API"""
    # No printers in environment no chance of getting one
    # Test only that printer doesn't exist
    assert UEM.get_printer(0) is False


def test_move_og():
    """Test moving a device through multiple OGs"""
    change_og_id = UEM.find_og(
        name=OG_TO_MOVE_TO)['OrganizationGroups'][0]['Id']

    # Move device to the root OG to start with
    UEM.move_og(ROOT_OG_ID, serial_number=TEST_DEVICE_SERIAL)
    assert UEM.get_device(
        serial_number=TEST_DEVICE_SERIAL)['LocationGroupName'] == ROOT_OG

    # Move device to the Staging OG
    UEM.move_og(change_og_id, serial_number=TEST_DEVICE_SERIAL)
    assert UEM.get_device(
        serial_number=TEST_DEVICE_SERIAL)['LocationGroupName'] == OG_TO_MOVE_TO

    # Move device back to the root OG to finish up
    UEM.move_og(ROOT_OG_ID, serial_number=TEST_DEVICE_SERIAL)
    assert UEM.get_device(
        serial_number=TEST_DEVICE_SERIAL)['LocationGroupName'] == ROOT_OG


def test_format_new_og():
    """Test formatting a payload for OG creation"""

    # Format the expected format
    example_payload = {}
    example_payload['LocationGroupType'] = 'Container'
    example_payload['Name'] = SESSION_ID
    example_payload['GroupId'] = SESSION_ID
    example_payload['Country'] = 'Australia'
    example_payload['Locale'] = 'en-AU'
    example_payload['Timezone'] = 57

    # Test the function
    payload = UEM.format_og_payload(SESSION_ID,
                                    SESSION_ID,
                                    "Container",
                                    "Australia",
                                    "en-AU",
                                    timezone=57)

    assert payload == example_payload

    payload = UEM.format_og_payload(SESSION_ID,
                                    SESSION_ID,
                                    "Container",
                                    "Australia",
                                    "en-AU",
                                    default_location="Test",
                                    devices=999,
                                    timezone=57,
                                    enable_api=True)

    example_payload['AddDefaultLocation'] = "Test"
    example_payload['Devices'] = 999
    example_payload['Timezone'] = 57
    example_payload['EnableRestApiAccess'] = True

    assert payload == example_payload


def test_create_og():
    """Test creating an OG"""

    # Create the payload
    payload = UEM.format_og_payload("CI Test - %s" % SESSION_ID,
                                    SESSION_ID,
                                    "Container",
                                    country="Australia",
                                    locale="en-AU",
                                    timezone=57)

    # Create the payload
    response = UEM.create_og(ROOT_OG_ID, payload)

    assert isinstance(response['Id'], int)

    assert len(
        UEM.find_og(name="CI Test - %s" %
                    SESSION_ID)['OrganizationGroups']) == 1

    # Test duplicate name fail
    assert UEM.create_og(ROOT_OG_ID, payload) is False

    # Test duplicate group ID fail
    payload['Name'] = "Unique"
    assert UEM.create_og(ROOT_OG_ID, payload) is False

    # Test blank payload
    # TODO: Fix
    # assert UEM.create_og(ROOT_OG_ID, "") is False


def test_delete_og():
    """Test deleting OG created during this session"""

    # Find the created OG
    og_uuid = UEM.find_og(name="CI Test - %s" %
                          SESSION_ID)['OrganizationGroups'][0]['Uuid']

    # Delete the OG
    assert UEM.delete_og(og_uuid) is True

    # Make sure it was deleted
    assert UEM.find_og(name="CI Test - %s" %
                       SESSION_ID)['OrganizationGroups'] == []


# TODO add reprocess coverage
# def reprocess_product(self, product_id, device_list, force=True):


def test_tidy_up():  # pragma: no cover
    """Delete any leftover artifacts from tests"""

    print("\nGroups")
    groups = UEM.find_group(name="CI Test - ")
    if groups is not None:
        for group in groups["SmartGroups"]:
            print("%s:\t%s" % (group["Name"], group["SmartGroupID"]))
            if UEM.delete_group(group["SmartGroupID"]):
                print("\tDeleted")

    print("\nProducts")
    products = UEM.find_product(name="CI Test - ")
    if products is not None:
        for product in products["Products"]:
            print("%s:\t%s" % (product["Name"], product["ID"]["Value"]))
            UEM.remove_all_groups_from_product(product["ID"]["Value"])
            if UEM.delete_product(product["ID"]["Value"]):
                print("\tDeleted")

    print("\nTags")
    tags = UEM.find_tag("CI Test - ")
    if tags is not None:
        for tag in tags:
            print("%s:\t%s" % (tag["TagName"], tag["Id"]["Value"]))
            if UEM.delete_tag(tag["Id"]["Value"]):
                print("\tDeleted")

    print("\nOGs")
    ogs = UEM.find_og("CI Test - ")['OrganizationGroups']
    if ogs is not None:
        for og in ogs:
            print("%s:\t%s" % (og["Name"], og["Uuid"]))
            if UEM.delete_og(og["Uuid"]):
                print("\tDeleted")

    assert True

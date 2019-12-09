"""Automated testing for WSO"""
import re
import json
import argparse
import requests
import random
import string
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
    assert pytest_wrapped_e.value.code == 1


def test_good_config_folder():
    """Tests good config"""

    assert isinstance(WSO('config').system_info(), dict)


def test_create_headers():
    """Test assembling the header structure"""
    # TODO: Stage creation of config
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
    info = UEM.system_info()
    assert isinstance(info, dict) is True


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
    QS = UEM.querystring(user=user,
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
    assert len(QS) == 3
    assert QS["page"] == page
    assert QS["pagesize"] == pagesize
    assert QS["user"] == user

def test_simple_get():
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
    assert response["headers"]["authorization"] == AUTH.encode(RANDOM_USERNAME, RANDOM_PASSWORD)
    assert response["headers"]["aw-tenant-code"] == RANDOM_TENANTCODE

    # Check v1
    response = wso.simple_get("/headers/", version=1)
    assert response["headers"]["accept"] == "application/json;version=1"
    assert response["headers"]["authorization"] == AUTH.encode(RANDOM_USERNAME, RANDOM_PASSWORD)
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
    response = wso.simple_get("/status/204", querystring=querystring, version=1)

def test_get_product_name():
    """Tests resolving a product id to a name"""
    assert UEM.get_product_name(TEST_PRODUCT_ID) == TEST_PRODUCT_NAME
    assert UEM.get_product_name("BADPRODUCT") is False

def test_get_group_name():
    """Tests resolving a group id to a name"""
    assert UEM.get_group_name(TEST_GROUP_ID) == TEST_GROUP_NAME
    assert UEM.get_group_name("BADGROUP") is False

# def test_filter_locals():
#     test = WSO.filter_locals(self="Test")
#     test2 = WSO.filter_locals(test="123")

#     pass

def test_remaining_api_calls():
    """Checks remaining API calls"""
    assert isinstance(UEM.remaining_api_calls(), int) is True

"""
    def filter_locals(self, _locals):
    def system_info(self):
    def find_og(self, name=None, pagesize=500, page=0):
    def get_og(self, group_id: int):
    def get_all_ogs(self, pagesize=500, page=0):
    def bulk_limits(self):
    def device_counts(self, organizationgroupid=None):
    def get_group(self, group_id: int, pagesize=500, page=0):

def test_get_group():
    "Tests getting group info""
    assert isinstance(AW.get_group(TEST_GROUP_NAME), dict) is True
    assert isinstance(AW.get_group(groupid=TEST_GROUP_ID), dict) is True

    def find_group(self, name=None, pagesize=500, page=0):
    def find_product(self, name, smartgroupid=None, pagesize=500, page=0):
    def get_product(self, product_id: int):
    def get_product_device_state(self,
    def get_product_assigned_groups(self, product_id: int):
    def product_is_active(self, product_id):
    def xctivate_product(self, action: str, product_id: int, skip_check: bool):
    def activate_product(self, product_id, skip_check=False):
    def deactivate_product(self, product_id, skip_check=True):
    def delete_product(self, product_id):
    def get_device(self,
    def get_all_devices(self,
    def get_device_ip(self, serial_number=None, device_id=None):
    def get_device_extensive(self,
    def assign_group_to_product(self, product_id: int, group_id: int):
    def check_no_group_assignments(self, product_id):
    def remove_group_from_product(self, product_id, group_id):
    def remove_all_groups_from_product(self, product_id):
    def create_group(self, name, payload):
    def create_group_from_devices(self, name, device_list):
    def create_group_from_ogs(self, name, og_list):
    def format_group_payload_devices(self, group_name, serial_list):
    def format_group_payload_ogs(self, group_name, og_list):
    def delete_group(self, group_id):
    def get_tag(self, name=None, org_group=None):
    def add_tag(self, tag_id: int, devices: list):
    def remove_tag(self, tag_id: int, devices: list):
    def x_tag(self, action, tag_id: int, devices: list):
    def get_tagged_devices(self, tag_id: int):
    def create_tag(self, tagname: str, org_group=None, tagtype=1):
    def delete_tag(self, tagid: int):
    def get_printer(self, printerid: int):  # pragma: no cover
    def move_og(self, deviceid, org_group: int, searchby='Serialnumber'):
    def reprocess_product(self, product_id, device_list, force=True):
"""

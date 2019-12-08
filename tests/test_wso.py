"""Automated testing for WSO"""
import re
import json
import random
import string
import pytest
from reqrest import REST
from basic_auth import Auth
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


# Random ID for the session
def random_chars(string_length=8):
    """Generate a random string of letters and digits """
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for i in range(string_length))


SESSION_ID = random_chars()

# Get AW version from API help page
#
config = Auth().read_config("uem.json")
URL = config['url']

# TODO fix proxy settings
# with open('config/proxy.json') as json_file:
#     settings = json.load(json_file)
#     proxy = settings['proxy']
#     if proxy:
#         proxies = {
#             'http': '%s:%s' % (settings['proxy_server'], settings['proxy_port']),
#             'https': '%s:%s' % (settings['proxy_server'], settings['proxy_port'])
#         }
#     else:
#         proxies = None

# Create REST instance
vREST = REST(url=URL)  #, proxy=proxies)

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
    AIRWATCH_VERSION = re.match(r'(AirWatch|VMware Workspace ONE UEM);(.*)',
                                VERSION, re.M | re.I).group(2)

print('Test session ID: %s' % SESSION_ID)
print('Testing WSO UEM Version: %s' % VERSION)

UEM = WSO()

# Random int / str generators


def random_string(string_length=15):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))


def random_number():
    """Generate a random string of fixed length """
    return random.randint(0, 9999)


# Tests


def test_bad_config_folder():
    """Tests bad config"""
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        WSO('notexistantfolder')
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1


# def test_debug_print(capsys):
#     """Test the debug printing function"""
#     message = random_string()

#     with capsys.disabled():
#         wso_quiet = WSO(debug=False)
#         wso_debug = WSO(debug=True)

#     wso_quiet.debug_print(message)
#     captured = capsys.readouterr()
#     assert captured.out == ""

#     wso_debug.debug_print(message)
#     captured = capsys.readouterr()
#     assert captured.out == message + "\n"


def test_create_headers():
    """Test assembling the header structure"""
    # TODO: Stage creation of config
    # Test v1
    headers = UEM.create_headers(version=1)

    assert headers["Accept"] == "application/json;version=1"
    assert headers[
        "Authorization"] == "Basic cHl0ZXN0OmJtakg2d2VXbGVVUjltUTgycTZJbmFJWlJSNGpmUTF4a2Qx"
    assert headers["Content-Type"] == 'application/json'
    assert headers[
        "aw-tenant-code"] == '9mMZzHvGdpz7yXiMM1rZjLNT3KW7X44ygmmRMeXwCjQ='

    # Try again with v2
    headers = UEM.create_headers()

    assert headers["Accept"] == "application/json;version=2"
    assert headers[
        "Authorization"] == "Basic cHl0ZXN0OmJtakg2d2VXbGVVUjltUTgycTZJbmFJWlJSNGpmUTF4a2Qx"
    assert headers["Content-Type"] == 'application/json'
    assert headers[
        "aw-tenant-code"] == '9mMZzHvGdpz7yXiMM1rZjLNT3KW7X44ygmmRMeXwCjQ='


def test_import_proxy():
    """Test importing the proxy settings"""
    # TODO: Import proxy settins to test
    proxy = UEM.import_proxy()
    assert proxy is None


def test_system_info():
    info = UEM.system_info()
    assert isinstance(info, dict) is True

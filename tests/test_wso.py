"""Automated testing for WSO"""
import random
import string
import pytest
from basic_auth import Auth
from wso.wso import WSO

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
    assert headers["Authorization"] == "Basic Y2l0ZXN0czpodW50ZXIy"
    assert headers["Content-Type"] == 'application/json'
    assert headers["aw-tenant-code"] == 'shibboleet'

    # Try again with v2
    headers = UEM.create_headers()

    assert headers["Accept"] == "application/json;version=2"
    assert headers["Authorization"] == "Basic Y2l0ZXN0czpodW50ZXIy"
    assert headers["Content-Type"] == 'application/json'
    assert headers["aw-tenant-code"] == 'shibboleet'


def test_import_proxy():
    """Test importing the proxy settings"""
    # TODO: Import proxy settins to test
    proxy = UEM.import_proxy()
    assert proxy is None

def test_system_info():
    info = UEM.system_info()
    assert isinstance(info, dict) is True

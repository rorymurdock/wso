"""Built tests"""
import os
import stat
import mock
import base64
import string
import random
from setup import ConfigSetup
#TODO: Setup main tests and stdin tests

SETUP = ConfigSetup(overwrite=True)

def random_string(string_length=15):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))

KEY = random_string()
VALUE = random_string()

def test_create_file_to_delete():
    """Tests writing json to a file"""
    assert SETUP.write_config({random_string(): random_string()}, 'testing') is True

def test_no_file():
    """Deletes a file"""
    if os.path.isfile('config/testing'):
        os.remove('config/testing')
    assert SETUP.check_file_exists('testing') is False

def test_wrong_file():
    """Tests for not existant file"""
    assert SETUP.check_file_exists('filedoesntexist') is False

def test_create_file():
    """Tests writing json to a file"""
    assert SETUP.write_config({KEY: VALUE}, 'testing') is True

def test_create_file_exception():
    """Tests writing to a readonly file"""
    SETUP.write_config({"file": "readonly"}, 'readonly')

    # Make file only
    os.chmod("config/readonly", stat.S_IREAD)

    assert SETUP.write_config("readonly", 'readonly') is False

    # Change file to make writeable
    os.chmod("config/readonly", stat.S_IWRITE)

def test_file():
    """Tests if file exists"""
    assert SETUP.check_file_exists('testing') is True

def test_get_file_contents():
    """Tests the contents of the file"""
    contents = SETUP.open_file("testing")
    assert contents[KEY] == VALUE


def test_get_file_wrong_file():
    """Tests opening non existing file"""
    assert SETUP.open_file("filedoesntexist") is False

def test_get_config_setting():
    """Tests verifying config"""
    assert SETUP.verify_config("testing", KEY, VALUE) is True
    assert SETUP.get_config_setting("testing") == {KEY: VALUE}
    assert SETUP.get_config_setting("filedoesntexist", key="wrongkey") == None

def test_get_config_setting_mismatch():
    """Tests handling non existant config"""
    assert SETUP.verify_config("testing", "keydoesntexist", "wrongvalue") is False
    assert SETUP.verify_config("testing", KEY, "wrongvalue") is False

def test_set_proxy_config():
    """Tests writing proxy config"""
    proxy_server = random_string()
    proxy_port = random.randint(0,65535)
    assert SETUP.write_proxy_config(proxy_server, proxy_port) is True
    assert SETUP.verify_config("proxy.json", "proxy", True) is True
    assert SETUP.verify_config("proxy.json", "proxy_server", proxy_server) is True
    assert SETUP.verify_config("proxy.json", "proxy_port", proxy_port) is True

    assert SETUP.write_proxy_config() is True
    assert SETUP.verify_config("proxy.json", "proxy", False) is True

def test_set_auth_config():
    """Tests writing auth config"""
    url = random_string()
    username = random_string()
    password = random_string()
    tenantcode = random_string()

    encoded_credentials = base64.b64encode(
        (username+":"+password).encode('utf-8')
    )
    authorization = "Basic "+encoded_credentials.decode('utf-8')

    assert SETUP.write_auth_config(url, authorization, tenantcode) is True
    assert SETUP.verify_config("uem.json", "url", url) is True
    assert SETUP.verify_config("uem.json", "Authorization", authorization) is True
    assert SETUP.verify_config("uem.json", "aw-tenant-code", tenantcode) is True

def test_set_all_config_existing():
    """Writes all config to files"""
    assert SETUP.set_config() is True

def test_unwriteable_dir():
    assert ConfigSetup(overwrite=True, config_dir='/').create_config_directory() is False

def test_write_config_no_folder():
    assert ConfigSetup(overwrite=True, config_dir='/').write_config(None, 'CI Tests') is False

#TODO create_config_directory()
#TODO write_config() 

# def test_cleanup_tests():
#     """Deletes all files created during testing"""
#     files = ("testing", "readonly", "proxy.json", "uem.json")
#     directories = ("config", "config/bad_config", "config/proxy_config")
    
#     for directory in directories:
#         temp_setup = ConfigSetup(config_dir=directory)
#         for file in files:
#             if temp_setup.check_file_exists(file):
#                 os.remove("%s/%s" % (directory, file))
#             assert temp_setup.check_file_exists(file) is False
#         if temp_setup.check_config_dir_exists():
#             os.rmdir(directory)
#         assert SETUP.check_config_dir_exists(directory) is False
    


# TODO: Try mock to do user input
# def test_set_all_config_fresh():
#     """Writes all config to files"""
#     SETUP.set_config()

"""Automated testing for configuring WSO"""
import os
import copy
import string
import random
import argparse
from io import StringIO

from basic_auth import Auth
from wso.configure import Config

CONFIG_DIR = "config-tests"

# Init package
AUTH = Auth(config_dir=CONFIG_DIR)
WSO_CONFIG = Config(config_dir=CONFIG_DIR)


# Random int / str generators
def random_string(string_length=15):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(string_length))


def random_number():
    """Generate a random string of fixed length """
    return random.randint(0, 9999)


# Create some random values to use for testing
RANDOM_URL = "cn%i.awmdmtest.com" % random_number()
RANDOM_USERNAME = random_string(8)
RANDOM_PASSWORD = random_string()
RANDOM_TENANTCODE = random_string()
RANDOM_PROXYSERVER = random_string(8)
RANDOM_PROXYPORT = random_number()

# Build the data structure expected
EXPECTED_RESULT = {}
EXPECTED_RESULT['authorization'] = AUTH.encode(RANDOM_USERNAME,
                                               RANDOM_PASSWORD)
EXPECTED_RESULT['url'] = RANDOM_URL
EXPECTED_RESULT['aw-tenant-code'] = RANDOM_TENANTCODE

# Build the data structure expected inc proxy
EXPECTED_RESULT_PROXY = copy.deepcopy(EXPECTED_RESULT)
EXPECTED_RESULT_PROXY['proxyserver'] = RANDOM_PROXYSERVER
EXPECTED_RESULT_PROXY['proxyport'] = RANDOM_PROXYPORT

# Print data used
print("Using generated data:")
print("\tURL: %s" % RANDOM_URL)
print("\tUsername: %s" % RANDOM_USERNAME)
print("\tPassword: %s" % RANDOM_PASSWORD)
print("\tAW Tenant Code: %s" % RANDOM_TENANTCODE)


# Test STD in
def test_interactive_data_encode(monkeypatch):
    """Test entering details via std in"""

    # Stage the std in data
    url = StringIO('%s\n%s\n%s\n%s\n\n%s\n' %
                   (RANDOM_URL, RANDOM_USERNAME, RANDOM_PASSWORD,
                    RANDOM_TENANTCODE, CONFIG_DIR))

    # Send std in and run the main function
    monkeypatch.setattr('sys.stdin', url)
    data = WSO_CONFIG.interactive()

    # Compare the data structure generated against the static build
    assert data == EXPECTED_RESULT


# Test STD in
def test_interactive_data_encode_w_proxy(monkeypatch):
    """Test entering details via std in"""

    # Stage the std in data
    url = StringIO(
        '%s\n%s\n%s\n%s\n%s\n%s\n%s' %
        (RANDOM_URL, RANDOM_USERNAME, RANDOM_PASSWORD, RANDOM_TENANTCODE,
         RANDOM_PROXYSERVER, RANDOM_PROXYPORT, CONFIG_DIR))

    # Send std in and run the main function
    monkeypatch.setattr('sys.stdin', url)
    data = WSO_CONFIG.interactive()

    # Compare the data structure generated against the static build
    assert data == EXPECTED_RESULT_PROXY


def test_arguments_data_encode():
    """Test mocking the arguments and writing the config"""
    args = argparse.Namespace(url=RANDOM_URL,
                              username=RANDOM_USERNAME,
                              password=RANDOM_PASSWORD,
                              tenantcode=RANDOM_TENANTCODE)

    result = WSO_CONFIG.arguments(args)

    assert result == EXPECTED_RESULT


def test_arguments_data_encode_w_proxy():
    """Test mocking the arguments and writing the config"""
    args = argparse.Namespace(url=RANDOM_URL,
                              username=RANDOM_USERNAME,
                              password=RANDOM_PASSWORD,
                              tenantcode=RANDOM_TENANTCODE,
                              proxyserver=RANDOM_PROXYSERVER,
                              proxyport=RANDOM_PROXYPORT,
                              directory=CONFIG_DIR)

    result = WSO_CONFIG.arguments(args)

    assert result == EXPECTED_RESULT_PROXY


def test_main_arguments():
    """Test mocking the arguments and running them through main()"""
    args = argparse.Namespace(url=RANDOM_URL,
                              username=RANDOM_USERNAME,
                              password=RANDOM_PASSWORD,
                              tenantcode=RANDOM_TENANTCODE,
                              directory=CONFIG_DIR)
    result = Config(config_dir=CONFIG_DIR, output="wso_args.json").main(args)

    assert result is True


def test_main_arguments_w_proxy():
    """Test mocking the arguments and running them through main()"""
    args = argparse.Namespace(url=RANDOM_URL,
                              username=RANDOM_USERNAME,
                              password=RANDOM_PASSWORD,
                              tenantcode=RANDOM_TENANTCODE,
                              proxyserver=RANDOM_PROXYSERVER,
                              proxyport=RANDOM_PROXYPORT,
                              directory=CONFIG_DIR)
    result = Config(config_dir=CONFIG_DIR,
                    output="wso_args_proxy.json").main(args)

    assert result is True


def test_main_interactive(monkeypatch):
    """Test mocking the std in and writing the config"""
    url = StringIO('%s\n%s\n%s\n%s\n\n%s\n' %
                   (RANDOM_URL, RANDOM_USERNAME, RANDOM_PASSWORD,
                    RANDOM_TENANTCODE, CONFIG_DIR))

    # Send std in and run the main function
    monkeypatch.setattr('sys.stdin', url)

    # Stage the empty args
    args = argparse.Namespace(url=None,
                              username=None,
                              password=None,
                              tenantcode=None)

    result = Config(config_dir=CONFIG_DIR,
                    output="wso_interactive.json").main(args)

    assert result is True


def test_main_interactive_w_proxy(monkeypatch):
    """Test mocking the std in and writing the config"""
    url = StringIO(
        '%s\n%s\n%s\n%s\n%s\n%s\n\n%s' %
        (RANDOM_URL, RANDOM_USERNAME, RANDOM_PASSWORD, RANDOM_TENANTCODE,
         RANDOM_PROXYSERVER, RANDOM_PROXYPORT, CONFIG_DIR))

    # Send std in and run the main function
    monkeypatch.setattr('sys.stdin', url)

    # Stage the empty args
    args = argparse.Namespace(url=None,
                              username=None,
                              password=None,
                              tenantcode=None,
                              proxyserver=None,
                              proxyport=None)

    result = Config(config_dir=CONFIG_DIR,
                    output="wso_interactive_proxy.json").main(args)

    assert result is True


def test_file_data_arguments():
    """Verify the data written via mock arguments"""
    filename = 'wso_args.json'
    assert AUTH.check_file_exists(filename) is True

    assert AUTH.verify_config(filename, 'authorization',
                              AUTH.encode(RANDOM_USERNAME,
                                          RANDOM_PASSWORD)) is True
    assert AUTH.verify_config(filename, 'url', RANDOM_URL) is True
    assert AUTH.verify_config(filename, 'aw-tenant-code',
                              RANDOM_TENANTCODE) is True


def test_file_data_arguments_w_proxy():
    """Verify the data written via mock arguments"""
    filename = 'wso_args_proxy.json'
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


def test_file_data_interactive():
    """Verify the data written via mock std in"""
    filename = 'wso_interactive.json'
    assert AUTH.check_file_exists(filename) is True

    assert AUTH.verify_config(filename, 'authorization',
                              AUTH.encode(RANDOM_USERNAME,
                                          RANDOM_PASSWORD)) is True
    assert AUTH.verify_config(filename, 'url', RANDOM_URL) is True
    assert AUTH.verify_config(filename, 'aw-tenant-code',
                              RANDOM_TENANTCODE) is True


def test_file_data_interactive_w_proxy():
    """Verify the data written via mock std in"""
    filename = 'wso_interactive_proxy.json'
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


def test_main_results():
    """Test the results of the real arguments"""
    # Due to complexities testing with arguments to get full coverage
    # run the script externally with full arguments
    os.popen('python3 -m pip install -e .')
    os.popen('python3 wso/configure.py -url cn1234.awtest.com\
             -username citests -password hunter2 -tenantcode shibboleet -directory %s'
             % CONFIG_DIR).read()

    filename = "uem.json"

    assert AUTH.check_file_exists(filename) is True
    assert AUTH.verify_config(filename, 'authorization',
                              AUTH.encode("citests", "hunter2")) is True
    assert AUTH.verify_config(filename, 'url', "cn1234.awtest.com") is True
    assert AUTH.verify_config(filename, 'aw-tenant-code', "shibboleet") is True

"""Uses config setup but with arguments"""
import os
import argparse
from configure import ConfigSetup

PARSER = argparse.ArgumentParser()

REQUIRED = PARSER.add_argument_group('Required arguments')
OPTIONAL = PARSER.add_argument_group('Optional arguments')

REQUIRED.add_argument("-url", help="WSO UEM URL", required=True)
REQUIRED.add_argument("-username", help="WSO UEM user", required=True)
REQUIRED.add_argument("-password", help="WSO UEM password", required=True)
REQUIRED.add_argument("-tenantcode", help="WSO UEM tenant code", required=True)
OPTIONAL.add_argument("--proxyurl", help="proxy server url")
OPTIONAL.add_argument("--proxyport", help="proxy server port")
ARGS = PARSER.parse_args()

SETUP = ConfigSetup()

print("Writing auth")

if not SETUP.write_auth_config(
        ARGS.url,
        SETUP.encode_credential(
            ARGS.username,
            ARGS.password),
        ARGS.tenantcode
    ):
    print("Fatal error writing config")
    os.sys.exit(1)

print("Writing proxy")
if not SETUP.write_proxy_config(
        ARGS.proxyurl,
        ARGS.proxyport
    ):
    print("Fatal error writing config")
    os.sys.exit(1)

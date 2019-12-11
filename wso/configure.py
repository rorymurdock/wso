"""Configure Auth for WSO UEM"""
import argparse
import logging
from basic_auth import Auth

LOG_LEVEL = logging.INFO


class Config():
    """Configure Auth for WSO UEM"""
    def __init__(self, config_dir="config", output="uem.json"):
        logging.basicConfig(format='%(levelname)s\t%(funcName)s\t%(message)s',
                            level=LOG_LEVEL)

        # If arguments are used it's passed as None
        if config_dir is None:
            config_dir = "config"

        # Create logging functions
        self.debug = logging.debug
        self.info = logging.info
        self.warning = logging.warning
        self.error = logging.error
        self.critical = logging.critical

        self.output = output
        self.auth = Auth(config_dir=config_dir)

    def filter_locals(self, _locals):
        """Filter some args from local()"""
        _list = []
        _list.append("self")

        for _item in _list:
            try:
                del _locals[_item]
            except KeyError:
                pass

        return _locals

    def interactive(self):
        """Ask the user for the information and format the config"""
        # Get data from user
        url = self.auth.ask("WSO UEM URL")
        username = self.auth.ask("WSO UEM Username")
        password = self.auth.ask("WSO UEM Password")
        tenant_code = self.auth.ask("WSO UEM Tenant code")
        proxyserver = self.auth.ask("Proxy server (leave blank for none)")

        if proxyserver != "":
            proxyport = self.auth.ask("Proxy port")

        config_dir = self.auth.ask("Config dir (leave blank for \"config\")")

        if config_dir == "":
            config_dir = "config"

        # TODO: Merge into one function
        # Encode data into base64
        encoded = self.auth.encode(username, password)

        # Generate data structure
        data = self.auth.basic_config_generate(url, encoded)

        # Add the tentant code
        data['aw-tenant-code'] = tenant_code

        # Add the proxy settings
        if proxyserver != "":
            data['proxyserver'] = proxyserver
            data['proxyport'] = int(proxyport)

        # Return the completed data
        self.info(data)
        return data

    def arguments(self, args):
        """Using data from the arguments format the config"""
        url = args.url
        username = args.username
        password = args.password
        tenant_code = args.tenantcode
        try:
            proxyserver = args.proxyserver
            proxyport = args.proxyport
        except AttributeError:
            proxyserver = None
            proxyport = None

        # Encode data into base64
        encoded = self.auth.encode(username, password)

        # Generate data structure
        data = self.auth.basic_config_generate(url, encoded)

        # Add the tentant code
        data['aw-tenant-code'] = tenant_code

        # Add the proxy settings
        if proxyserver is not None:
            data['proxyserver'] = proxyserver
            data['proxyport'] = proxyport

        # Return the completed data
        return data

    def write_data(self, data, filename):
        """Write the config to a file"""
        write = self.auth.write_config(data, filename)

        return write

    def get_args(self):  # pragma: no cover
        """Parse arguments and return the namespace"""
        # This is indirectly tested by the test_main_results() funtion
        parser = argparse.ArgumentParser()
        optional = parser.add_argument_group('Optional arguments')

        optional.add_argument("-url", help="WSO UEM URL")
        optional.add_argument("-username", help="WSO UEM user")
        optional.add_argument("-password", help="WSO UEM password")
        optional.add_argument("-tenantcode", help="WSO UEM tenant code")
        optional.add_argument("-proxyserver", help="Proxy server")
        optional.add_argument("-proxyport", help="Proxy port")
        optional.add_argument("-directory", help="Config dir")
        args = parser.parse_args()

        return args

    def main(self, args):
        """Main function"""
        # Check for args
        if None in (args.url, args.username, args.password, args.tenantcode):
            # Run in interactive mode
            print("No arguments found or missing arguments\n\
                Running in interactive mode")
            print("Run with -h for more info")
            data = self.interactive()
        else:
            # Use arguments
            data = self.arguments(args)

            # Set config dir
            if args.directory:
                self.directory = args.directory

        # Write the config to file
        if self.write_data(data, self.output):
            print("Config sucessfully written")
            return True

        # Issue writing to file
        print("Unable to write config")  # pragma: no cover
        return False  # pragma: no cover


# This is indirectly tested by the test_main_results() funtion
if __name__ == "__main__":  # pragma: no cover
    # Get args if any
    ARGS = Config().get_args()

    # Get and write config
    Config(config_dir=ARGS.directory).main(ARGS)

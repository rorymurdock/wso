"""Configure Auth for WSO UEM"""
import argparse
from basic_auth import Auth

AUTH = Auth()


class Config():
    """Configure Auth for WSO UEM"""
    def __init__(self, output="uem.json"):
        self.output = output

    def interactive(self):
        """Ask the user for the information and format the config"""
        # Get data from user
        url = AUTH.ask("AirWatch URL")
        username = AUTH.ask("AirWatch Username")
        password = AUTH.ask("AirWatch Password")
        tenant_code = AUTH.ask("AirWatch Tenantcode")
        proxyserver = AUTH.ask("Proxy server (leave blank for none)")

        if proxyserver != "":
            proxyport = AUTH.ask("Proxy port")

        # TODO: Merge into one function
        # Encode data into base64
        encoded = AUTH.encode(username, password)

        # Generate data structure
        data = AUTH.basic_config_generate(url, encoded)

        # Add the tentant code
        data['aw-tenant-code'] = tenant_code

        # Add the proxy settings
        if proxyserver != "":
            data['proxyserver'] = proxyserver
            data['proxyport'] = int(proxyport)

        # Return the completed data
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
        encoded = AUTH.encode(username, password)

        # Generate data structure
        data = AUTH.basic_config_generate(url, encoded)

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
        write = AUTH.write_config(data, filename)

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
        args = parser.parse_args()

        return args

    def main(self, args):
        """Main function"""
        # Check for args
        if None in (args.url, args.username, args.password, args.tenantcode):
            # Run in interactive mode
            print(
                "No arguments found or missing arguments\n\
                Running in interactive mode"
            )
            print("Run with -h for more info")
            data = self.interactive()
        else:
            # Use arguments
            data = self.arguments(args)

        # Write the config to file
        if self.write_data(data, self.output):
            print("Config sucessfully written")
            return True

        # Issue writing to file
        print("Unable to write config")  # pragma: no cover
        return False  # pragma: no cover


# This is indirectly tested by the test_main_results() funtion
if __name__ == "__main__":  # pragma: no cover
    ARGS = Config().get_args()
    Config().main(ARGS)

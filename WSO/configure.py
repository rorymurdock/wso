"""Configure proxy and auth config required for UEM"""
import os
import json
import base64

## This will setup your proxy and credentials json files
class ConfigSetup():
    """Class for setting up config"""
    def __init__(self, overwrite=False, config_dir="config", auth_file="uem.json", proxy_file="proxy.json"):
        ## Config paths
        self.overwrite = overwrite
        self.config_dir = config_dir
        self.auth_file = auth_file
        self.proxy_file = proxy_file
        self.proxy = None
        self.proxy_server = None
        self.proxy_port = None
        self.url = None
        self.tenantcode = None
        self.authorization = None

    def return_conf_file_list(self):
        """Returns config file names"""
        return {self.auth_file, self.proxy_file}

    def check_config_dir_exists(self, directory=None):
        """Checks if the config exists"""
        if directory is None:
            directory = self.config_dir
        return os.path.isdir(directory)

    def create_config_directory(self):
        """Create config directory"""
        try:
            os.mkdir(self.config_dir)
            print("Config directory created")
            return True
        except (IOError, PermissionError):
            print("Unable to create directory\nCheck permissions")
            return False

    def check_file_exists(self, config_file):
        """Check if file exists"""
        return os.path.isfile(self.config_dir+"/"+config_file)

    def write_config(self, data, out_file):
        """Write config to file"""
        if not self.check_config_dir_exists():
            print("Config directory doesn't exist")
            if not self.create_config_directory():
                os.sys.exit()

        try:
            with open(self.config_dir+'/'+out_file, 'w') as outfile:
                json.dump(data, outfile)
        except (IOError, PermissionError):
            print("Unable to write to config file %s, check permissions" % (
                self.config_dir+'/'+out_file))
            return False

        if os.path.isfile(self.config_dir+'/'+out_file):
            return True

    def open_file(self, file):
        """Open file and return contents in json"""
        try:
            with open(self.config_dir+'/'+file) as json_file:
                return json.load(json_file)

        except (PermissionError, IOError, FileNotFoundError):
            return False

    def verify_config(self, file, key, value):
        """Verify if a key is in a file and check value"""
        contents = self.open_file(file)
        try:
            if contents[key] == value:
                return True
            else:
                return False
        except (TypeError, KeyError):
            return False

    def get_config_setting(self, file, key=None):
        """Gets a key from a file and returns it"""
        contents = self.open_file(file)
        try:
            if key is None:
                return contents
            else:
                return contents[key]
        except (KeyError, TypeError):
            return None

    def write_proxy_config(self, proxyserver=None, proxyport=None):
        """Write config for proxy"""
        if None in (proxyserver, proxyport):
            proxies = {
                "proxy": False
            }
        else:
            proxies = {
                "proxy": True,
                "proxy_server": proxyserver,
                "proxy_port": proxyport
            }

        return self.write_config(proxies, self.proxy_file)

    def write_auth_config(self, url, authorization, tenantcode):
        """Write config for auth"""
        config = {
            "url": url,
            "Authorization": authorization,
            "aw-tenant-code": tenantcode
        }

        return self.write_config(config, self.auth_file)

    def check_setting(self, message, key):
        """Get config, if blank ask and write to file"""
        for file in self.return_conf_file_list():
            config = self.get_config_setting(file, key)
            if config is not None:
                return config

        if self.overwrite is True: # pragma: no cover
            config = input(message+": ")
            return str(config)
        return None

    def encode_credential(self, username, password):
        """Encodes credentials into b64"""
        creds = base64.b64encode(
            (username+":"+password).encode('utf-8')
        )

        decoded_creds = creds.decode()
        return "Basic " + decoded_creds

    def decode_credential(self, authorization):
        """Encodes credentials into b64"""

        creds = base64.b64decode(
            (authorization).encode('utf-8')
        )

        decoded_creds = creds.decode()
        return decoded_creds

    def set_config(self):
        """Sets config and checks if not set asks"""
        # Verify proxy settings
        self.proxy = self.check_setting("Proxy True/False", "proxy")
        if self.proxy is True:  # pragma: no cover
            self.proxy_server = self.check_setting("Proxy Server", "proxy_server")
            self.proxy_port = self.check_setting("Proxy Port", "proxy_port")

        # Verify uem settings
        self.url = self.check_setting("URL", "url")
        self.tenantcode = self.check_setting("Tenant Code", "aw-tenant-code")
        self.authorization = self.check_setting("", 'Authorization')
        self.authorization = self.authorization.replace('Basic ', '')

        encoded_credentials = self.decode_credential(self.authorization).split(':')
        username = encoded_credentials[0]
        password = encoded_credentials[1]

        # Encode username + password into base64
        encoded_credentials = self.encode_credential(username, password)

        # Set auth
        self.authorization = encoded_credentials

        # If overwrite then write to files
        if bool(self.overwrite):
            if self.proxy == "True": # pragma: no cover
                # Write proxy
                self.write_proxy_config(proxyserver=self.proxy_server, proxyport=self.proxy_port)
            else:
                # Write "proxy": False
                self.write_proxy_config()

            self.authorization = self.encode_credential(username, password)

            # Write UEM config
            return self.write_auth_config(
                url=self.url,
                authorization=self.authorization,
                tenantcode=self.tenantcode
                )

if __name__ == "__main__": # pragma: no cover   
    # Init class
    SETUP = ConfigSetup()

    SETUP.set_config()

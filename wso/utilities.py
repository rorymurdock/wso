"""A collection of utilities used in WSO"""
import sys
import json
from basic_auth import Auth

CONFIG_FILES = {
    "application_state": "device_application_status.json",
    "device_models": "device_models.json",
    "device_ownership": "device_ownership.json",
    "locales": "locale.json",
    "os_ids": "os_ids.json",
    "platforms": "platforms.json",
    "timezones": "timezones.json"
}


class Utils:
    "WSO utils"

    def __init__(self):
        for file in CONFIG_FILES:
            if not Auth(config_dir="wso/system_parameters").check_file_exists(
                    CONFIG_FILES[file]):
                sys.exit("Unable to load file %s" % file)

    def check_key(self, t_key, value, file):
        """A varible function to check the keys of a json for a value"""
        with open("wso/system_parameters/" + CONFIG_FILES[file]) as json_file:
            keys = json.load(json_file)

        for key in keys:
            for nested_key in keys[key]:
                if value == nested_key[t_key]:
                    return True
        return False

    # TODO Complete funcitons
    def check_countries(self, country):
        """Check if a country is valid"""
        pass

    def check_timezone(self, timezone):
        """Check if a timezone code is valid"""
        return self.check_key("id", timezone, 'timezones')

    def check_locale(self, lang):
        """Check if a locale code is valid"""
        return self.check_key("locale_code", lang, 'locales')

    def lookup_application_status(self, status):
        """Lookup an application status from its ID"""
        pass

    def check_operating_system_id(self, os_id):
        """Checks an OS ID is valid"""
        pass

    def lookup_operating_system(self, os_id):
        """Lookup an operating system from its ID"""
        pass

    def check_device_model(self, dm_id):
        """Checks a device ID is valid"""
        pass

    def lookup_device_model(self, dm_id):
        """Lookup a device model from its ID"""
        pass

    def check_ownership_type(self, o_type):
        """Checks an ownership type is valid"""
        pass

    def check_platform_id(self, pid):
        """Checks a platform ID is valid"""
        pass

    def lookup_platform_id(self, pid):
        """Lookup a platform from its ID"""
        pass

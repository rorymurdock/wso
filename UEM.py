import os
import sys
import json
import time
from REST import REST

# In the event UEM has support for API v1 & 2
# the highest available version is used


class UEM():
    """WSO UEM APIs, the easy way"""
    # Default to v2 API, allow overrides
    def __init__(self, debug=False):

        ## Config files
        self.config_dir = "config"
        self.config_file = "uem.json"
        self.proxy_file = "proxy.json"
        self.debug = debug

        # Import settings from config files
        config = self.import_config(self.config_file)
        headers_v1 = self.create_headers(
            config,
            1)

        self.rest_v1 = REST(
            url=config['url'],
            headers=headers_v1,
            proxy=self.import_proxy()
            )

        headers_v2 = self.create_headers(
            config,
            2)

        self.rest_v2 = REST(
            url=config['url'],
            headers=headers_v2,
            proxy=self.import_proxy()
            )

    def str_to_json(self, string):
        try:
            return json.loads(string)
        except json.decoder.JSONDecodeError:
            print("Object is not json")
            return None

    # Check HTTP codes for common errors
    # Allow specifying an expected code for custom use
    def check_http_response(self, status_code, expected_code=None):
        if status_code == expected_code:
            return True
        elif status_code == 200:
            if self.debug:
                print('HTTP 200\nOK')
            return True
        elif status_code == 201:
            if self.debug:
                print('HTTP 201\nCreated')
            return True
        elif status_code == 204:
            if self.debug:
                print('HTTP 204\nEmpty response')
            return True
        elif status_code == 401:
            print('HTTP 401\nCheck AirWatch Credentials')
            return False
        elif status_code == 403:
            print('HTTP 403\nPermission denied, check AW permissions')
            return False
        elif status_code == 404:
            print('HTTP 404\nNot found')
            return False
        elif status_code == 422:
            print('HTTP 422\nInvalid SearchBy Parameter')
            return False
        else:
            print('Unknown code %s' % status_code)
            return False

    # Import credentials config file
    def import_config(self, file):
        if os.path.isfile(self.config_dir+"/"+file):
            with open(self.config_dir+'/'+file) as json_file:
                return json.load(json_file)
        else:
            print("Unable to open config file, run setup.py")
            sys.exit()

    # Import proxy from config file
    def import_proxy(self):
        proxy = self.import_config(self.proxy_file)

        if proxy['proxy'] == "True":
            if self.debug:
                print("Using proxy %s:%s" % (proxy['proxy_server'], proxy['proxy_port']))
            proxies = {
                'http': proxy['proxy_server']+':'+proxy['proxy_port'],
                'https': proxy['proxy_server']+':'+proxy['proxy_port']
            }
        else:
            if self.debug:
                print("Not using proxy")
            proxies = None

        return proxies

    # Combine varibles to form headers
    def create_headers(self, config, version):
        if self.debug:
            print("Using API Version: %s" % version)
        headers = {
            'Accept': "application/json;version=%s" % version,
            'aw-tenant-code': config['aw-tenant-code'],
            'Authorization': config['Authorization'],
            'Content-Type': "application/json"
        }

        return headers

    def append_url(self, url, variables):
        for variable in variables:
            if variable not in ("self", "url") and variables[variable] is not None:
                #TODO: regex for URL %s?%s=%s
                if "?" not in url:
                    url = "%s?%s=%s" % (url, variable, variables[variable])
                else:
                    url = "%s&%s=%s" % (url, variable, variables[variable])
        if self.debug:
            print("URL: %s" % url)
        return url

    def basic_url(self, url):
        # Query API
        response = self.rest_v2.get(url)

        # Check response and return validated data
        check = self.check_http_response(response.status_code)

        if check:
            return self.str_to_json(response.text), response.status_code
        else:
            return False, response.status_code

    ##### Web Calls #####
    def remaining_api_calls(self):
        response = self.rest_v2.get('/api/system/info')

        print(response)
        print(response.status_code)

        check = self.check_http_response(response.status_code)
        if check:
            # Examples of what you can do
            if self.debug:
                for key in (
                        "X-RateLimit-Remaining",
                        "X-RateLimit-Limit",
                        "X-RateLimit-Reset"
                    ):
                    print("%s: %s" % (key, response.headers[key]))
                print(
                    "Limit resets at %s" % time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(
                            int(response.headers['X-RateLimit-Reset']))
                        )
                    )

                print("%s Used" % "{:.1%}".format(
                    1-(
                        int(response.headers['X-RateLimit-Remaining'])
                        /
                        int(response.headers['X-RateLimit-Limit'])
                    )
                ))

            return int(response.headers['X-RateLimit-Remaining'])

        else:
            print("Error getting response header")
            return False

    def system_info(self):
        response = self.rest_v2.get(
            '/api/system/info')

        if self.check_http_response(response.status_code):
            return json.loads(response.text)
        else:
            print('Error gettting System version')

    def get_og(self, name=None, page_size=500, page=0):
        # Set base URL
        url = '/api/system/groups/search'

        # Add arguments
        url = self.append_url(url, vars())

        # Query API
        response = self.rest_v1.get(url)

        # Check response and return validated data
        check = self.check_http_response(response.status_code)
        if check:
            return self.str_to_json(response.text)
        else:
            print('Error gettting OG info')
            return False

"""UEM Python Module"""
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
    def __init__(
            self,
            config_dir="config",
            auth_file="uem.json",
            proxy_file="proxy.json",
            debug=False
    ):

        ## Config files
        self.config_dir = config_dir
        self.auth_file = auth_file
        self.proxy_file = proxy_file
        self.debug = debug

        # Import settings from config files
        config = self.import_config(self.auth_file)

        # Create v1 API object
        headers_v1 = self.create_headers(
            config,
            1)

        self.rest_v1 = REST(
            url=config['url'],
            headers=headers_v1,
            proxy=self.import_proxy(),
            debug=debug
            )

        # Create v2 API object
        headers_v2 = self.create_headers(
            config,
            2)

        self.rest_v2 = REST(
            url=config['url'],
            headers=headers_v2,
            proxy=self.import_proxy(),
            debug=debug
            )

    def str_to_json(self, string):
        """Tries to convert str to json dict, returns None on failure"""
        try:
            return json.loads(string)
        except json.decoder.JSONDecodeError:
            print("Object is not json")
            return None

    # Check HTTP codes for common errors
    # Allow specifying an expected code for custom use
    def check_http_response(self, status_code, expected_code=None):
        """Checks if response is a expected or a known good response"""
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
        elif status_code == 400:
            if self.debug:
                print('HTTP 400\nBad request')
            return False
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
        """Imports config from config_dir / file and returns json of config."""
        if os.path.isfile(self.config_dir+"/"+file):
            with open(self.config_dir+'/'+file) as json_file:
                return json.load(json_file)
        else:
            print("Unable to open config file, run setup.py")
            sys.exit(1)

    # Import proxy from config file
    def import_proxy(self):
        """Imports proxy from config_dir / file and returns proxy json of config"""
        proxy = self.import_config(self.proxy_file)

        if proxy['proxy'] is True:
            if self.debug:
                print("Using proxy %s:%s" % (proxy['proxy_server'], proxy['proxy_port']))
            proxies = {
                'http': '%s:%s' % (proxy['proxy_server'], proxy['proxy_port']),
                'https': '%s:%s' % (proxy['proxy_server'], proxy['proxy_port'])
            }
        else:
            if self.debug:
                print("Not using proxy")
            proxies = None

        return proxies

    # Combine varibles to form headers
    def create_headers(self, config, version):
        """Creates headers for REST API Call using config and version"""
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
        """Appends search terms to a URL. Returns a url str"""
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
        """Basic REST GET returns [json response, status code]"""
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
        """Gets the number of API calls remaining, returns int"""
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
        """Gets system information, returns json of system info"""
        response = self.rest_v2.get(
            '/api/system/info')

        if self.check_http_response(response.status_code):
            return json.loads(response.text)
        else:
            print('Error gettting System version')
            return False

    def get_og(self, name=None, pagesize=500, page=0):
        """Gets OGs, supports all or searching, returns json"""
        # Set base URL
        url = '/api/system/groups/search'

        # Add arguments
        url = self.append_url(url, vars())

        # Query API
        response = self.rest_v2.get(url)

        # Check response and return validated data
        check = self.check_http_response(response.status_code)
        if check:
            return self.str_to_json(response.text)
        else:
            print('Error gettting OG info')
            return False

    def get_group(self, name=None, pagesize=500, page=0):
        """Gets smartgroups, supports all or searching, returns json"""
        # Set base URL
        url = '/api/mdm/smartgroups/search'

        # Add arguments
        url = self.append_url(url, vars())

        # Query API
        response = self.rest_v1.get(url)

        # Check response and return validated data
        check = self.check_http_response(response.status_code)
        if check:
            return self.str_to_json(response.text)
        else:
            print('Error gettting Group info')
            return False

    def get_name(self, item_type, item_id):
        """Appends item_type and item_id to base URL and returns the Name key"""
        response = self.rest_v1.get(
            '/api/mdm/%s/%s' % (item_type, item_id))

        if self.check_http_response(response.status_code):
            return self.str_to_json(response.text)['Name']
        else:
            print('Error gettting %s %s name' % (item_type, item_id))
            return False

    def get_product_name(self, product_id):
        """Resolves a product ID to name"""
        return self.get_name("products", product_id)

    def get_group_name(self, group_id):
        """Resolves a smartgroup ID to a name"""
        return self.get_name("smartgroups", group_id)

    def search_product(self, name):
        """Search for product by name"""
        url = '/api/mdm/products/search?name=%s' % name

        return self.basic_url(url)


    def get_product_assigned_groups(self, product_id):
        """Gets all assigned groups for a productId"""
        #TODO: Complete
        # Set base URL
        url = '/api/mdm/products/%i' % product_id
        # Query API
        response = self.basic_url(url)

        if response[0] is not False:
            return response[0]['SmartGroups']
        else:
            return False
        # if response is not False:
        #     return response
        # else:
        #     print('Error gettting device smart groups')


    def activate_product(self, product_id, skip_check=False):
        """Activates a product based on ID, returns Bool"""
        # Check that there is at least 1 group assigned
        if not self.get_product_assigned_groups(product_id) and skip_check is False:
            print("There are no smart groups assigned to %s, unable to activate" %
                  self.get_product_name(product_id))
            return False

        # Set base URL
        url = '/api/mdm/products/%i/activate' % product_id

        # Query API
        response = self.rest_v1.post(url, None)
        if self.check_http_response(response) is not False:
            return response
        else:
            print('Error activating product %i' % product_id)
            return False

    # Create
    def create_product(self, name, description, action_type_id, action_item_id, platform_id):
        """Creates a product using fileId, actionType.
         Product will be inactive and has no assigned groups. Returns int of new ID"""
        # Product action
        action = {}
        # 5
        action['ActionTypeId'] = action_type_id
        # Item ID
        # Unable to create files using API
        # File must exist already
        action['ItemId'] = action_item_id
        # Persist post enterprise reset
        action['Persist'] = True

        payload = {}
        payload['Name'] = name

        # Set the product to be at the highest OG
        payload['ManagedByOrganizationGroupID'] = self.get_og(pagesize=1)['OrganizationGroups'][0]['Id']
        payload['Description'] = description

        # For safety all new products are inactive
        # Use activate_product and assign_group functions
        payload['Active'] = False

        # PlatformIds
        # 5 = Android
        payload['PlatformId'] = platform_id
        payload['SmartGroups'] = []
        payload['Manifest'] = {}
        payload['Manifest']['Action'] = []
        payload['Manifest']['Action'].append(action)

        if self.debug:
            print("Create product: %s" % payload)

        if self.search_product(name)[1] == 204:
            if self.debug:
                print("Product %s does not exist" % name)
            response = self.rest_v1.post('/api/mdm/products/create', payload)
            return self.str_to_json(response.text)['Value']
        else:
            print("Product already exists, unable to create")
            return False

    def delete_product(self, product_id):
        """Delete a product based on ID"""
        product_name = self.get_product_name(product_id)
        if product_name is False:
            print("Error product %s doesn't exist" % product_id)
        else:
            print("Deleting product %s" % product_name)
            if self.check_http_response(
                    self.rest_v1.delete('/api/mdm/products/%i' % product_id).status_code
                ):
                print("Product %s deleted" % product_name)
                return True
            else:
                print("Unable to delete %s" % product_name)
        return False

    def get_all_devices(self):
        #TODO Add pagesize
        """Get all devices from AirWatch"""
        return self.basic_url('/api/mdm/devices/search')[0]

    def get_product(self, product_id):
        """Return product details from ID"""
        return self.basic_url('/api/mdm/products/%i' % product_id)

    def get_device_ip(self, serialNumber):
        """Get device IP from serial"""
        # TODO: add more search parameters
        response = self.basic_url('/api/mdm/devices/network/?searchBy=Serialnumber&id=%s' % serialNumber)
        if response[0] is not False:
            return response[0]['IPAddress']['WifiIPAddress']
        else:
            return False

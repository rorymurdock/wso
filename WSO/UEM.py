"""UEM Python Module"""
import os
import sys
import json
import time
from .configure import ConfigSetup
from reqREST import REST

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

    class Response:
        """returns a tuple i.e. response.text"""
        def __init__(self,
                     success=None,
                     status_code=None,
                     message=None,
                     id=None,
                     json=None,
                     value=None
                     ):

            self.success = success
            self.status_code = status_code
            self.message = message
            self.id = id
            self.json = json
            self.value = value

    def debug_print(self, message):
        """If debugging is enabled print message"""
        if self.debug:
            print(message)

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
        status_codes = {}
        status_codes[200] = True, 'HTTP 200: OK'
        status_codes[201] = True, 'HTTP 201: Created'
        status_codes[204] = True, 'HTTP 204: Empty Response'
        status_codes[400] = False, 'HTTP 400: Bad Request'
        status_codes[401] = False, 'HTTP 401: Check WSO Credentials'
        status_codes[403] = False, 'HTTP 403: Permission denied'
        status_codes[404] = False, 'HTTP 404: Not found'
        status_codes[406] = True, 'HTTP 406: Not Acceptable'
        status_codes[422] = False, 'HTTP 422: Invalid searchby Parameter'
        status_codes[500] = False, 'HTTP 500: Internal server error'


        if status_code == expected_code:
            return True
        elif status_code in status_codes:
            self.debug_print(status_codes[status_code][1])
            return status_codes[status_code][0]
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
            print("Unable to open config file, run configure.py")
            sys.exit(1)
            #TODO Setup config during init
            # ConfigSetup().set_config()
            # if os.path.isfile(self.config_dir+"/"+file):
            #     with open(self.config_dir+'/'+file) as json_file:
            #         return json.load(json_file)


    # Import proxy from config file
    def import_proxy(self):
        """Imports proxy from config_dir / file and returns proxy json of config"""
        proxy = self.import_config(self.proxy_file)

        if proxy['proxy'] is True:
            self.debug_print("Using proxy %s:%s" % (proxy['proxy_server'], proxy['proxy_port']))
            proxies = {
                'http': '%s:%s' % (proxy['proxy_server'], proxy['proxy_port']),
                'https': '%s:%s' % (proxy['proxy_server'], proxy['proxy_port'])
            }
        else:
            self.debug_print("Not using proxy")
            proxies = None

        return proxies

    # Combine varibles to form headers
    def create_headers(self, config, version=2):
        """Creates headers for REST API Call using config and version"""
        self.debug_print("Using API Version: %s" % version)
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
        self.debug_print("URL: %s" % url)
        return url

    def basic_url(self, url, expected_code=None):
        """Basic REST GET returns [json response, status code]"""
        # Query API
        response = self.rest_v2.get(url)

        # Check response and return validated data
        check = self.check_http_response(response.status_code, expected_code=expected_code)

        if check:
            if not isinstance(response.text, dict):
                return self.str_to_json(response.text), response.status_code
            else:
                return response.text, response.status_code
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
        if check and response.status_code != 204:
            return self.str_to_json(response.text)
        else:
            print('Error gettting OG info %s' % name)
            return False

    def get_group(self, name=None, groupid=None, pagesize=500, page=0):
        """Gets smartgroups, supports all or searching, returns json"""
        # Set base URL
        url = '/api/mdm/smartgroups/'
        
        if groupid is not None and isinstance(groupid, int):
            url = url + str(groupid)
        else:
            url = url + "search"

        # Add arguments
        url = self.append_url(url, vars())

        # Query API
        response = self.rest_v1.get(url)

        # Check response and return validated data
        check = self.check_http_response(response.status_code)
        if check and response.status_code != 204:
            return self.str_to_json(response.text)
        else:
            self.debug_print('Error getting Group info')
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

    def get_product(self, name):
        """Search for product by name"""
        url = '/api/mdm/products/search?name=%s' % name

        return self.basic_url(url)

    def get_product_assigned_groups(self, product_id):
        """Gets all assigned groups for a productId"""
        response = self.basic_url('/api/mdm/products/%i' % product_id)

        if response[0] is not False:
            if response[0]['SmartGroups'] == []:
                self.debug_print('Product %s has no assigned groups' % product_id)
            return response[0]['SmartGroups']
        else:
            return False

    def product_is_active(self, product_id):
        """Checks if a product is active, returns BOOL"""
        response = self.basic_url('/api/mdm/products/%s' % product_id)

        if response[0] is not False:
            if response[0]['Active'] is True:
                self.debug_print('Product %s is active' % product_id)
                return True
            elif response[0]['Active'] is False:
                self.debug_print('Product %s is inactive' % product_id)
                return False

    def xctivate_product(self, action, product_id, skip_check):
        """Activates or Deactivates a product based on ID, returns Bool"""
        # Check that there is at least 1 group assigned
        if not self.get_product_assigned_groups(product_id) and skip_check is False:
            print("There are no smart groups assigned to %s, unable to activate" %
                  self.get_product_name(product_id))
            return False

        product_state = self.product_is_active(product_id)

        if (product_state and action == 'activate') or (not product_state and action == 'deactivate'):
            self.debug_print('Product is already in the desired state')
            return True

        # Set base URL
        url = '/api/mdm/products/%i/%s' % (product_id, action)

        # Query API
        response = self.rest_v1.post(url)
        if self.check_http_response(response.status_code) is not False:
            print(response)
            return True
        else: # pragma: no cover
            print('Error trying to %s product %i' % (action, product_id))
            return False
         #TODO: fix issue with auto act/deact set in console

    def activate_product(self, product_id, skip_check=False):
        """Activates a product"""
        print('Activating product %s' % self.get_product_name(product_id))
        return self.xctivate_product('activate', product_id, skip_check)

    def deactivate_product(self, product_id, skip_check=True):
        """Deactivates a product"""
        print('Dectivating product %s' % self.get_product_name(product_id))
        #TODO Check for auto / semi auto activation
        return self.xctivate_product('deactivate', product_id, skip_check)

    # Create
    def create_product(self, name, description, action_type_id, action_item_id, platform_id):
        """Creates a product using fileId, actionType.
         Product will be inactive and has no assigned groups. Returns int of new ID"""
        # Product action
        action = {}

        action['ActionTypeId'] = action_type_id
        # Item ID
        # Unable to create files using API
        # File must exist already
        action['ItemId'] = action_item_id

        # Persist post enterprise reset
        action['Persist'] = 'True'

        payload = {}
        payload['Name'] = name

        # Set the product to be at the highest OG
        payload['ManagedByOrganizationGroupID'] = self.get_og(pagesize=1)['OrganizationGroups'][0]['Id']
        payload['Description'] = description

        # For safety all new products are inactive
        # Use activate_product and assign_group functions
        payload['Active'] = 'False'

        # PlatformIds
        # 5 = Android
        payload['PlatformId'] = platform_id
        payload['SmartGroups'] = []
        payload['Manifest'] = {}
        payload['Manifest']['Action'] = []
        payload['Manifest']['Action'].append(action)

        self.debug_print("Create product: %s" % payload)

        product_name = self.get_product(name)[1]

        if  product_name == 204 or product_name == 404:
            self.debug_print("Product %s does not exist" % name)
            response = self.rest_v1.post('/api/mdm/products/create', payload)
            print("error: %s" % response.text)
            print(response.status_code)
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
            response = self.rest_v1.delete('/api/mdm/products/%i' % product_id)
            if self.check_http_response(
                    response.status_code
                ):
                print("Product %s deleted" % product_name)
                return True
            else:
                print("Unable to delete %s" % product_name)
                self.debug_print(response.text)
        return False

    def get_all_devices(self):
        #TODO Add pagesize
        """Get all devices from AirWatch"""
        return self.basic_url('/api/mdm/devices/search')[0]

    def get_product_by_id(self, product_id):
        """Return product details from ID"""
        return self.basic_url('/api/mdm/products/%s' % product_id)

    def get_device_ip(self, serial_number):
        """Get device IP from serial"""
        # TODO: add more search parameters
        response = self.basic_url('/api/mdm/devices/network/?searchBy=Serialnumber&id=%s' % serial_number)
        if response[0] is not False:
            return response[0]['IPAddress']['WifiIPAddress']
        else:
            return False

    def get_device(self, serial_number):
        """Get device details from serial"""
        response = self.basic_url('/api/mdm/devices/serialnumber/%s' % serial_number)

        return response[0]

        # if response[0] is not False:
        #     return response[0]
        # else:
        #     return response[0]
    
    # TODO Build out
    def get_device_extensive(self, device_id):
        response = self.basic_url('/api/mdm/devices/extensivesearch?deviceid=%s' % device_id)

        return response[0]

    def assign_group_to_product(self, product_id, group_id):
        """Assigns a group to a product"""
        # Get product current assignments
        # Check group is not already assigned
        # Assign group

        # Check group and product are valid
        group_name = self.get_group_name(group_id)
        product_name = self.get_product_name(product_id)
        print('Assigning group %s to product %s' % (group_id, product_name))

        if not group_name:
            self.debug_print('Invalid group Id')
            return False

        if not product_name:
            self.debug_print('Invalid product Id')
            return False

        assigned_groups = self.get_product_assigned_groups(product_id)

        # Check if group is already assigned
        for group in assigned_groups:
            if group['SmartGroupId'] == group_id:
                self.debug_print('Smart group %s already assigned to %s' % (product_id, group_id))
                return True

        self.debug_print('Assigning %s to %s' % (group_name, product_name))
        response = self.rest_v1.post('/api/mdm/products/%s/addsmartgroup/%s' % (product_id, group_id))

        return self.check_http_response(response.status_code)

    def check_no_group_assignments(self, product_id):
        """Checks if product has no assignemnts"""
        if self.get_product_assigned_groups(product_id) == []:
            return True
        return False

    def remove_group_from_product(self, product_id, group_id):
        """Removes the specified group from a product"""
        print("Removing group %s from %s" % (self.get_group_name(group_id), self.get_product_name(product_id)))
        response = self.rest_v1.post('/api/mdm/products/%s/removesmartgroup/%s' % (product_id, group_id))

        # Check response
        if self.check_http_response(response.status_code):
            return True
        else:
            return False

    def remove_all_groups_from_product(self, product_id):
        """Remove all assigned groups from products"""
        product_name = self.get_product_name(product_id)

        if not product_name:
            self.debug_print('Invalid product Id')
            return False

        assigned_groups = self.get_product_assigned_groups(product_id)

        if assigned_groups == []:
            self.debug_print('Product has no assigned groups, nothing to do')
            return True

        for group in assigned_groups:
            print('Removing %s:%s from %s' % (group['SmartGroupId'], group['Name'], product_name))
            response = self.remove_group_from_product(product_id, group['SmartGroupId'])
            if response:
                print('%s:%s removed from %s successfully' % (group['SmartGroupId'], group['Name'], product_name))

        if self.get_product_assigned_groups(product_id) == []:
            # Product has no groups, removal was successful
            return True

    def create_group(self, name, payload):
        """Create a group from a payload"""
        # Check group doesn't already exist
        if self.get_group(name=name) is not False:
            print('Error group already exists')
            return self.Response(success=False, message='Error group already exists')

        response = self.rest_v1.post('/api/mdm/smartgroups/', payload=payload)

        if self.check_http_response(response.status_code):
            print('Group %s created successfully, id: %s' % (name, self.str_to_json(response.text)['Value']))
            return self.Response(success=True, id=self.str_to_json(response.text)['Value'])
        else: # pragma: no cover
            print('Error creating group %s' % name)
            return self.Response(success=False, message='Error creating group %s' % name)

    def create_group_from_devices(self, name, device_list):
        """Create a group from a list of devices"""
        # Format the list into the UEM payload
        payload = self.format_group_payload_devices(name, device_list)

        return self.create_group(name, payload)

    def create_group_from_ogs(self, name, og_list):
        """Create a group from a list of OGs"""
        # Format the list into the UEM payload
        payload = self.format_group_payload_ogs(name, og_list)

        return self.create_group(name, payload)

    def format_group_payload_devices(self, group_name, serial_list):
        """Create a group from a list of serials"""
        payload = {}
        payload['Name'] = group_name
        payload['CriteriaType'] = 'UserDevice'
        payload['DeviceAdditions'] = []

        for serial in serial_list:
            device_response = self.get_device(serial)
            if device_response is not False:
                print('Device %s is valid' % serial)
            elif device_response is False:
                print('Warning: Device %s doesn\'t exist' % serial)
                continue

            device = {}
            device['Id'] = device_response['Id']['Value']
            device['Name'] = device_response['DeviceFriendlyName']
            payload['DeviceAdditions'].append(device)

        if payload['DeviceAdditions'] == []:
            print('No devices added to group %s' % group_name)

        return payload

    def format_group_payload_ogs(self, group_name, og_list):
        """Take a list of OGs and format it for a group POST req"""
        payload = {}
        payload['Name'] = group_name
        payload['CriteriaType'] = 'All'
        payload['OrganizationGroups'] = []

        for org_group in og_list:
            og_response = self.get_og(org_group)
            # if og_response is not False:
            if og_response['OrganizationGroups'] == []:
                print('Warning: OG %s doesn\'t exist' % org_group)
                continue
            else:
                print('OG %s is valid' % org_group)

            og_payload = {}
            og_payload['Id'] = og_response['OrganizationGroups'][0]['Id']
            og_payload['Name'] = og_response['OrganizationGroups'][0]['Name']
            og_payload['Uuid'] = og_response['OrganizationGroups'][0]['Uuid']
            payload['OrganizationGroups'].append(og_payload)

        if payload['OrganizationGroups'] == []:
            print('No OGs added to group %s' % group_name)

        return payload

    def delete_group(self, group_id):
        """Delete a group based on ID"""
        group_name = self.get_group_name(group_id)
        if group_name is False:
            print("Error group %s doesn't exist" % group_id)
        else:
            print("Deleting group %s" % group_name)
            response = self.rest_v1.delete('/api/mdm/smartgroups/%i' % group_id)
            if self.check_http_response(
                    response.status_code
                ):
                print("Group %s deleted" % group_name)
                return True
            else:
                print("Unable to delete %s" % group_name)
                self.debug_print(response.text)
        return False
    
    def get_tag(self, name=None, og=None):
        """Gets tags, supports all or searching, returns json"""

        arguments = {}

        if og is None:
            # Set the product to be at the highest OG
            arguments['OrganizationGroupId'] = self.get_og(pagesize=1)['OrganizationGroups'][0]['Id']
        if name is not None:
            arguments['name'] = name
        
        response = self.rest_v1.get("/api/mdm/tags/search", arguments)

        if self.check_http_response(response.status_code):
            response = json.loads(response.text)['Tags']

            return response

        return False # pragma: no cover
    
    def add_tag(self, tagid: int, devices: list):
        """Adds tags to device list, returns bool"""
        return self.x_tag('add', tagid, devices)
    
    def remove_tag(self, tagid: int, devices: list):
        """Removes tags from device list, returns bool"""
        return self.x_tag('remove', tagid, devices)
    
    def x_tag(self, action, tagid: int, devices: list):
        """Performs an action on device tags"""
        if action not in ['add', 'remove']:
            print('%s invalid action')
            return False

        payload = {}
        payload['BulkValues'] = {}
        payload['BulkValues']['Value'] = devices

        response = self.rest_v1.post('/api/mdm/tags/%i/%sdevices' % (tagid, action), payload=payload)
        
        return self.check_http_response(response.status_code)
    
    def get_tagged_devices(self, tagid: int):

        response = self.basic_url('/api/mdm/tags/%i/devices' % tagid)

        if response[1] == 200:
            return response[0]['Device']
        else:
            return False # pragma: no cover

    def create_tag(self, tagname: str, og=None, tagtype=1):
        
        existing_tag = self.get_tag(tagname)
        if existing_tag:
            print('Tag already exists: %s' % existing_tag[0]['Id']['Value'])
            return existing_tag[0]['Id']['Value']

        payload = {}

        if og is None:
            # Set the product to be at the highest OG
            payload['LocationGroupId'] = self.get_og(pagesize=1)['OrganizationGroups'][0]['Id']

        payload['TagName'] = tagname
        payload['TagType'] = tagtype
        
        response = self.rest_v1.post("/api/mdm/tags/addtag", payload)

        if self.check_http_response(response.status_code):
            return json.loads(response.text)['Value']

        return False # pragma: no cover
    
    def delete_tag(self, tagid: int):
        response = self.rest_v1.delete('/api/mdm/tags/%i' % tagid)

        return self.check_http_response(response.status_code)
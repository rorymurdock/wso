"""WSO UEM package for managing large WSO instances"""
import sys
import json
import time
import logging

from basic_auth import Auth
from reqrest import REST
from wso.utilities import Utils
from wso.configure import Config


class WSO():
    """WSO API facade"""
    def __init__(self,
                 config_dir="config",
                 config_file="uem.json",
                 debug=False,
                 bulk_query_trigger=50):

        # Sort out logging
        log_level = logging.ERROR
        if debug:
            log_level = logging.INFO

        logging.basicConfig(format='%(levelname)s\t%(funcName)s\t%(message)s',
                            level=log_level)

        # Create logging functions
        self.debug = logging.debug
        self.info = logging.info
        self.warning = logging.warning
        self.error = logging.error
        self.critical = logging.critical

        # Show sensitve info such as auth headers
        self.show_sensitive = False

        # Set max size line to log
        self.max_log = 9000

        # Set a limit of when to swtich to bulk querys
        self.bulk_query_trigger = bulk_query_trigger

        # Get config
        self.config_dir = config_dir
        self.config = Auth(config_dir).read_config(config_file)

        if not self.config:
            self.critical("Unable to get config, run configure.py")
            self.configure()
            self.critical("Run again to use config")
            sys.exit(1)

        self.info("Imported config - %s" % self.info_sensitive(self.config))

        # Create v1 API object
        headers_v1 = self.create_headers(version=1)

        self.rest_v1 = REST(url=self.config['url'],
                            headers=headers_v1,
                            proxy=self.import_proxy(),
                            debug=debug,
                            timeout=9999)

        # Create v2 API object
        headers_v2 = self.create_headers(version=2)

        self.rest_v2 = REST(url=self.config['url'],
                            headers=headers_v2,
                            proxy=self.import_proxy(),
                            debug=debug,
                            timeout=9999)

        self.utils = Utils()

    def configure(self):
        """Interactive setup of config"""
        # Write config if none present
        Config().main(Config().get_args())

    def info_sensitive(self, message):
        """Redacts the info if show sensitive is False"""
        if self.show_sensitive:
            return message
        else:
            return "Redacted for security"

    def create_headers(self, version=2):
        """Creates headers for REST API Call using config and version"""
        headers = {
            'Accept': "application/json;version=%s" % version,
            'aw-tenant-code': self.config['aw-tenant-code'],
            'Authorization': self.config['authorization'],
            'Content-Type': "application/json"
        }

        self.info("Generated v%i headers - %s" %
                  (version, self.info_sensitive(headers)))

        return headers

    # Import proxy from config file
    def import_proxy(self):
        """Imports proxy from config_dir / file and\
            returns proxy json of config"""

        # Try to read the proxy settings, if the key doesn't exist
        # assume no proxy is used
        try:
            self.debug("Using proxy %s:%s" %
                       (self.config['proxyserver'], self.config['proxyport']))
            proxies = {
                'http':
                '%s:%s' %
                (self.config['proxyserver'], self.config['proxyport']),
                'https':
                '%s:%s' %
                (self.config['proxyserver'], self.config['proxyport'])
            }
        except KeyError:
            self.debug("No proxy config found")
            proxies = None

        self.info("Generated proxy config - %s" % proxies)
        return proxies

    def check_http_response(self, response, expected_code=None):
        """Checks if response is a expected or a known good response"""
        self.info("args: %s" % self.filter_locals(locals()))

        status_codes = {}
        status_codes[200] = True, 'HTTP 200: OK'
        status_codes[201] = True, 'HTTP 201: Created'
        status_codes[204] = True, 'HTTP 204: Empty Response'
        status_codes[400] = False, 'HTTP 400: Bad Request'
        status_codes[401] = False, 'HTTP 401: Check WSO Credentials'
        status_codes[403] = False, 'HTTP 403: Permission denied'
        status_codes[404] = False, 'HTTP 404: Not found'
        status_codes[406] = False, 'HTTP 406: Not Acceptable'
        status_codes[422] = False, 'HTTP 422: Invalid searchby Parameter'
        status_codes[500] = False, 'HTTP 500: Internal server error'

        # Check if a HTTP code is a "good" code
        if response.status_code == expected_code:
            return True

        # Lookup the code in the dict
        elif response.status_code in status_codes:
            self.debug(status_codes[response.status_code][1])
            if response.status_code != 200:
                # Show the body for non 200
                self.debug(response.text)
            return status_codes[response.status_code][0]

        # Unable to find code return False
        else:
            self.error('Unknown code %s' % response.status_code)
            return False

    def str_to_json(self, string):
        """Tries to convert str to json dict, returns None on failure"""
        # If the args are too large don't display in the logger
        if sys.getsizeof(string) > self.max_log:
            self.info("args exceed max display size: %s" %
                      sys.getsizeof(string))
        else:
            self.info("args: %s" % self.filter_locals(locals()))
        # Convert into json, catch the exception
        try:
            converted = json.loads(string)
            self.info("Sucessfully converted str to dict")
            return converted

        # string isn't json
        except json.decoder.JSONDecodeError:
            self.error("Object is not json")

        return None

    def querystring(self, **kwargs):
        """Turns args into a querystring"""
        # kwargs is already in the right format just return that
        self.info("Kwargs - %s" % kwargs)

        for key, value in dict(kwargs).items():
            if value is None:
                del kwargs[key]

        self.info("Filtered args: %s" % kwargs)

        return kwargs

    def simple_get(self, path, querystring=None, version=2):
        """Simple HTTP get given a path"""
        # If the args are too large don't display in the logger
        if sys.getsizeof(self.filter_locals(locals())) > self.max_log:
            self.info("args exceed max display size %s" %
                      sys.getsizeof(self.filter_locals(locals())))
        else:
            self.info("args: %s" % self.filter_locals(locals()))

        # Query API
        if version == 2:
            response = self.rest_v2.get(path, querystring=querystring)
        else:
            response = self.rest_v1.get(path, querystring=querystring)

        # If the response is too large don't display in the logger
        size = sys.getsizeof(response.text)

        if size > self.max_log:
            self.info("Response body exceed max display size %s" % size)
        else:
            self.info("Response body - %s" % response.text)

        # Check response and return validated data
        check = self.check_http_response(response)
        if check and response.status_code != 204:
            return self.str_to_json(response.text)

        # 204 is no content, in WSO that's
        # usually no results found for searches
        elif check and response.status_code == 204:
            return None

        return False

    def get_name(self, item_type, item_id):
        """Appends item_type and item_id to base\
           URL and returns the Name key"""
        self.info("args: %s" % self.filter_locals(locals()))
        response = self.rest_v1.get('/api/mdm/%s/%s' % (item_type, item_id))

        if self.check_http_response(response):
            return self.str_to_json(response.text)['Name']
        else:
            self.error('Error gettting %s %s name' % (item_type, item_id))
            return False

    def get_product_name(self, product_id):
        """Resolves a product ID to name"""
        self.info("args: %s" % self.filter_locals(locals()))
        return self.get_name("products", product_id)

    def get_group_name(self, group_id):
        """Resolves a smartgroup ID to a name"""
        self.info("args: %s" % self.filter_locals(locals()))
        return self.get_name("smartgroups", group_id)

    def filter_locals(self, _locals):
        """Filter some args from local()"""
        _list = []
        _list.append("self")

        for _item in list(_list):
            try:
                del _locals[_item]
            except KeyError:
                pass

        return _locals

    # System calls

    def remaining_api_calls(self):
        """The number of API calls remaining, returns int"""

        # Do a call because we need the headers
        response = self.rest_v2.get('/api/system/info')

        # Print all of the relevant keys
        if self.check_http_response(response):
            for key in ("X-RateLimit-Remaining", "X-RateLimit-Limit",
                        "X-RateLimit-Reset"):
                self.info("%s: %s" % (key, response.headers[key]))

            # Workout when the limit resets
            self.info("Limit resets at %s" % time.strftime(
                '%Y-%m-%d %H:%M:%S',
                time.localtime(int(response.headers['X-RateLimit-Reset']))))

            # Show what % of calls have been used
            self.info("%s Used" % "{:.1%}".format(
                1 - (int(response.headers['X-RateLimit-Remaining']) /
                     int(response.headers['X-RateLimit-Limit']))))

            return int(response.headers['X-RateLimit-Remaining'])

        else:  # pragma: no cover
            self.error("Error getting response header")
            return False

    def system_info(self):
        """Returns the UEM sys info page"""
        # Set base URL
        url = '/api/system/info'

        return self.simple_get(url, version=1)

    def find_og(self, name=None, pagesize=500, page=0):
        """Find ogs based on name"""
        self.info("args: %s" % self.filter_locals(locals()))
        # Set base URL
        url = '/api/system/groups/search'

        # Add arguments
        querystring = self.querystring(name=name, pagesize=pagesize, page=page)

        return self.simple_get(url, querystring, 2)

    def get_og(self, group_id: int):
        """Abstract function of find_og()"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Set base URL
        url = '/api/system/groups/%i' % group_id

        return self.simple_get(url, version=1)

    def get_all_ogs(self, pagesize=500, page=0):
        """Abstract function of find_og()"""
        self.info("args: %s" % self.filter_locals(locals()))
        return self.find_og(pagesize=pagesize, page=page)

    # MDM Queries
    def bulk_limits(self):
        """Returns the UEM sys info page"""
        # Set base URL
        url = '/api/mdm/devices/bulksettings'

        return self.simple_get(url, version=1)

    def device_counts(self, organizationgroupid=None):
        """Returns the UEM sys info page"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Set base URL
        url = '/api/mdm/devices/devicecountinfo'

        # Add arguments
        querystring = self.querystring(organizationgroupid=organizationgroupid)

        return self.simple_get(url, querystring, 1)

    def get_group(self, group_id: int, pagesize=500, page=0):
        """Get a group from the ID"""
        self.info("args: %s" % self.filter_locals(locals()))
        # Set base URL
        url = '/api/mdm/smartgroups/%i' % group_id

        # Add arguments
        querystring = self.querystring(pagesize=pagesize, page=page)

        return self.simple_get(url, querystring, 1)

    def find_group(self, name=None, pagesize=500, page=0):
        """Find a group by name"""
        self.info("args: %s" % self.filter_locals(locals()))
        # Set base URL
        url = '/api/mdm/smartgroups/search'

        # Add arguments
        querystring = self.querystring(name=name, pagesize=pagesize, page=page)

        return self.simple_get(url, querystring, 1)

    def find_product(self, name, smartgroupid=None, pagesize=500, page=0):
        """Search for product by name"""
        self.info("args: %s" % self.filter_locals(locals()))
        # Set base URL
        url = '/api/mdm/products/search'

        # Add arguments
        querystring = self.querystring(name=name,
                                       smartgroupid=smartgroupid,
                                       pagesize=pagesize,
                                       page=page)

        return self.simple_get(url, querystring, 1)

    def get_product(self, product_id: int):
        """Get product by ID"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Set base URL
        url = '/api/mdm/products/%i' % product_id

        return self.simple_get(url, version=1)

    def get_product_device_state(self,
                                 product_id: int,
                                 state: str,
                                 pagesize=500,
                                 page=0):
        """Search for product by name"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Check if state is valid
        if state not in ['compliant', 'inprogress', 'failed', 'assigned']:
            self.error('Invalid state %s' % state)
            return None

        # Set base URL
        url = '/api/mdm/products/%i/%s' % (product_id, state)

        # Add arguments
        querystring = self.querystring(pagesize=pagesize, page=page)

        return self.simple_get(url, querystring, 2)

    def get_product_assigned_groups(self, product_id: int):
        """Gets all assigned groups for a product id, uses get_product()"""
        self.info("args: %s" % self.filter_locals(locals()))

        product = self.get_product(product_id)

        if product is not False:
            if product['SmartGroups'] == []:
                self.debug('Product %s has no assigned groups' % product_id)
            return product['SmartGroups']
        else:
            return False

    def product_is_active(self, product_id):
        """Checks if a product is active, returns Bool"""
        self.info("args: %s" % self.filter_locals(locals()))

        product = self.get_product(product_id)

        self.info(product['Active'])

        return product['Active']

    def xctivate_product(self, action: str, product_id: int, skip_check: bool):
        """Activates or Deactivates a product based on ID, returns Bool"""
        self.info("args: %s" % self.filter_locals(locals()))

        product = self.get_product(product_id)

        # Get current state
        product_state = product['Active']

        # Check if the product has auto de/activation
        try:
            activation = product['ActivationDateTime']
            deactivation = product['DeactivationDateTime']
        except KeyError:
            activation = None
            deactivation = None

        if activation is not None:
            print("%s has an auto activation enabled for %s" %
                  (product["Name"], activation))
            self.warning("%s has an auto activation enabled for %s" %
                         (product["Name"], activation))
        if deactivation is not None:
            print("%s has an auto deactivation enabled for %s" %
                  (product["Name"], deactivation))
            self.warning("%s has an auto deactivation enabled for %s" %
                         (product["Name"], deactivation))

        # print(datetime.datetime.strptime(activation, '%-m/%-d/%Y %H:%M:%S tt'))
        # TODO: Find fix for decimal m & d on all systems

        # Check that there is at least 1 group assigned
        if not self.get_product_assigned_groups(
                product_id) and skip_check is False and action == "activate":
            self.error(
                "There are no smart groups assigned to %s, unable to activate"
                % product['Name'])
            return False

        # Check if anything needs to be done
        if (product_state
                and action == 'activate') or (not product_state
                                              and action == 'deactivate'):
            self.warning('Product %s is already in the desired state' %
                         product["Name"])
            return True

        # Set base URL
        url = '/api/mdm/products/%i/%s' % (product_id, action)

        response = self.rest_v1.post(url)

        if self.check_http_response(response):
            self.info("%s has been %sd" % (product['Name'], action))
        else:  # pragma: no cover
            # Shouln't reach this state however log it just in case
            self.error("Unable to %s %s" % (action, product_id))

        return self.check_http_response(response)

    def activate_product(self, product_id, skip_check=False):
        """Activates a product"""
        print('Activating product %s' % self.get_product_name(product_id))
        return self.xctivate_product('activate', product_id, skip_check)

    def deactivate_product(self, product_id, skip_check=True):
        """Deactivates a product"""
        print('Dectivating product %s' % self.get_product_name(product_id))
        return self.xctivate_product('deactivate', product_id, skip_check)

    def delete_product(self, product_id):
        """Delete a product based on ID"""
        self.info("args: %s" % self.filter_locals(locals()))

        product_name = self.get_product_name(product_id)
        if product_name is False:
            self.error("Product %s doesn't exist" % product_id)

        if self.get_product_assigned_groups(product_id):
            self.critical("Product %s has groups assigned, unable to delete" %
                          product_id)
            return False

        else:
            self.debug("Deleting product %s" % product_name)
            response = self.rest_v1.delete('/api/mdm/products/%i' % product_id)
            self.info("Response body - %s" % response.text)

            if self.check_http_response(response):
                self.info("Product %s deleted" % product_name)
                print("Product %s deleted" % product_name)
                return True
            else:
                self.error("Unable to delete %s" % product_name)
        return False

    def get_device(self,
                   device_id=None,
                   macaddress=None,
                   udid=None,
                   serial_number=None,
                   imei=None,
                   eas_id=None,
                   pagesize=500,
                   page=0):
        """Get devices from AirWatch"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Set base URL
        url = '/api/mdm/devices'

        # Map ids against the WSO format
        ids = {}
        ids["DeviceId"] = device_id
        ids["Macaddress"] = macaddress
        ids["Udid"] = udid
        ids["Serialnumber"] = serial_number
        ids["ImeiNumber"] = imei
        ids["EasId"] = eas_id

        _id = None

        for _query in ids:
            if ids[_query] is not None:
                _id = _query
                break

        if _id is None:
            self.error("No device search parameters speficied")
            return False

        self.info("Searching by %s for %s" % (_id, ids[_id]))
        querystring = self.querystring(searchBy=_id,
                                       id=ids[_id],
                                       pagesize=pagesize,
                                       page=page)

        return self.simple_get(url, querystring, 1)

    def get_all_devices(self,
                        user=None,
                        model=None,
                        platform=None,
                        lastseen=None,
                        ownership=None,
                        lgid=None,
                        compliantstatus=None,
                        seensince=None,
                        orderby=None,
                        sortorder=None,
                        pagesize=500,
                        page=0):
        """Get all devices from AirWatch"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Set base URL
        url = '/api/mdm/devices/search'

        querystring = self.querystring(user=user,
                                       model=model,
                                       platform=platform,
                                       lastseen=lastseen,
                                       ownership=ownership,
                                       lgid=lgid,
                                       compliantstatus=compliantstatus,
                                       seensince=seensince,
                                       orderby=orderby,
                                       sortorder=sortorder,
                                       pagesize=pagesize,
                                       page=page)

        return self.simple_get(url, querystring, 1)

    def get_device_ip(self, serial_number=None, device_id=None):
        """Get device IP from serial"""
        self.info("args: %s" % self.filter_locals(locals()))

        if serial_number is None and device_id is None:
            self.error("No device search criteria specified")
            print("No device search criteria specified")
            return False

        if device_id is not None:
            self.info("Resolving device ID to serial")
            device = self.get_device(device_id=device_id)
            if device:
                self.debug("%s => %s" % (device_id, device["SerialNumber"]))
                serial_number = device["SerialNumber"]

        response = self.simple_get(
            '/api/mdm/devices/network/?searchBy=Serialnumber&id=%s' %
            serial_number)

        if response:
            ipaddr = response['IPAddress']['WifiIPAddress']
            self.info(ipaddr)
            return ipaddr

        return False

    def get_device_extensive(self,
                             device_id=None,
                             organizationgroupid=None,
                             platform=None,
                             startdatetime=None,
                             enddatetime=None,
                             customattributeslist=None,
                             enrollmentstatus=None,
                             statuschangestarttime=None,
                             statuschangeendtime=None,
                             macaddress=None,
                             page=None,
                             pagesize=None):
        """Get device using a varity of parameters"""
        self.info("args: %s" % self.filter_locals(locals()))

        url = "/api/mdm/devices/extensivesearch"

        ids = {}
        ids["DeviceId"] = device_id
        ids["organizationgroupid"] = organizationgroupid
        ids["platform"] = platform
        ids["startdatetime"] = startdatetime
        ids["enddatetime"] = enddatetime
        ids["customattributeslist"] = customattributeslist
        ids["enrollmentstatus"] = enrollmentstatus
        ids["statuschangestarttime"] = statuschangestarttime
        ids["statuschangeendtime"] = statuschangeendtime
        ids["macaddress"] = macaddress

        _id = None

        for _query in ids:
            if ids[_query] is not None:
                _id = _query
                break

        if _id is None:
            self.error("No device search parameters speficied")
            return False

        self.info("Searching by %s for %s" % (_id, ids[_id]))

        querystring = self.querystring(
            DeviceId=device_id,
            organizationgroupid=organizationgroupid,
            platform=platform,
            startdatetime=startdatetime,
            enddatetime=enddatetime,
            customattributeslist=customattributeslist,
            enrollmentstatus=enrollmentstatus,
            statuschangestarttime=statuschangestarttime,
            statuschangeendtime=statuschangeendtime,
            macaddress=macaddress,
            pagesize=pagesize,
            page=page)

        return self.simple_get(url, querystring, 1)

    def assign_group_to_product(self, product_id: int, group_id: int):
        """Assigns a group to a product"""
        self.info("args: %s" % self.filter_locals(locals()))
        # Get product current assignments
        # Check group is not already assigned
        # Assign group

        # Check group and product are valid
        group_name = self.get_group_name(group_id)
        product_name = self.get_product_name(product_id)
        print('Assigning group %s to product %s' % (group_id, product_name))

        if not group_name:
            self.error('Invalid group ID: %i' % group_id)
            return False

        if not product_name:
            self.error('Invalid product ID: %i' % product_id)
            return False

        assigned_groups = self.get_product_assigned_groups(product_id)

        # Check if group is already assigned
        for group in assigned_groups:
            if group['SmartGroupId'] == group_id:
                self.warning('Smart group %s already assigned to %s' %
                             (product_id, group_id))
                return True

        self.debug('Assigning %s to %s' % (group_name, product_name))
        response = self.rest_v1.post('/api/mdm/products/%s/addsmartgroup/%s' %
                                     (product_id, group_id))

        if self.check_http_response(response) and self.product_is_active(
                product_id):
            self.debug('Reprocessing product %s' % product_name)
            reprocess = self.reprocess_product(product_id=product_id,
                                               device_list=None,
                                               force=False)

            if reprocess:
                self.debug('Product %s reprocessed successfully' %
                           product_name)
            return reprocess

        # Encountered issue where groups would be assigned but the product not assigned
        # VMWare TDOC-6776
        # If we edit an existing Product created via API and add a component like F/A
        # or Application to it using API, the product is not pushed to Policy Engine.
        # Similarly when there is a smart group addition to an existing Product via
        #  API we do not queue jobs to the newly added devices until we do a subsequent
        # call to the /reprocess/ API. This behavior is expected and as per the design.

        return self.check_http_response(response)

    def check_no_group_assignments(self, product_id):
        """Checks if product has no assignemnts"""
        self.info("args: %s" % self.filter_locals(locals()))

        if self.get_product_assigned_groups(product_id) == []:
            return True
        return False

    def remove_group_from_product(self, product_id, group_id):
        """Removes the specified group from a product"""
        self.info("args: %s" % self.filter_locals(locals()))

        self.info(
            "Removing group %s from %s" %
            (self.get_group_name(group_id), self.get_product_name(product_id)))
        response = self.rest_v1.post(
            '/api/mdm/products/%s/removesmartgroup/%s' %
            (product_id, group_id))

        # Check response
        if self.check_http_response(response):
            self.info("%i removed from %i" % (group_id, product_id))
            return True
        else:  # pragma: no cover
            # Shouln't reach this state however log it just in case
            self.error("Unable to remove %i from %i" % (group_id, product_id))

        return False

    def remove_all_groups_from_product(self, product_id):
        """Remove all assigned groups from products"""
        self.info("args: %s" % self.filter_locals(locals()))

        product_name = self.get_product_name(product_id)

        if not product_name:
            self.error('Invalid product ID %s' % product_id)
            return False

        assigned_groups = self.get_product_assigned_groups(product_id)

        if assigned_groups == []:
            self.warning('Product has no assigned groups, nothing to do')
            return True

        for group in assigned_groups:
            self.debug('Removing %s:%s from %s' %
                       (group['SmartGroupId'], group['Name'], product_name))
            response = self.remove_group_from_product(product_id,
                                                      group['SmartGroupId'])
            if response:
                self.debug(
                    '%s:%s removed from %s successfully' %
                    (group['SmartGroupId'], group['Name'], product_name))

        if self.get_product_assigned_groups(product_id) == []:
            return True

        # Shouln't reach this state however log it just in case
        return False  # pragma: no cover

    def create_group(self, name, payload):
        """Create a group from a payload"""
        self.info("args: %s" % self.filter_locals(locals()))

        # TODO Add check for blank payload / check group size post creation

        # Check group doesn't already exist
        if self.find_group(name) is not None:
            self.error('Group %s already exists' % name)
            return False

        response = self.rest_v1.post('/api/mdm/smartgroups/', json=payload)

        if self.check_http_response(response):
            print('Group %s created successfully, id: %s' %
                  (name, self.str_to_json(response.text)['Value']))
            return self.str_to_json(response.text)['Value']
        else:  # pragma: no cover
            self.error('Error creating group %s' % name)
            return False

    def create_group_from_devices(self, name, device_list):
        """Create a group from a list of devices"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Format the list into the UEM payload
        payload = self.format_group_payload_devices(name, device_list)

        if payload:
            return self.create_group(name, payload)

        return False

    def create_group_from_ogs(self, name, og_list):
        """Create a group from a list of OGs"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Format the list into the UEM payload
        payload = self.format_group_payload_ogs(name, og_list)

        if payload:
            return self.create_group(name, payload)

        return False

    def format_group_payload_devices(self, group_name, serial_list):
        """Create a group from a list of serials"""
        self.info("args: %s" % self.filter_locals(locals()))

        payload = {}
        payload['Name'] = group_name
        payload['CriteriaType'] = 'UserDevice'
        payload['DeviceAdditions'] = []

        # Remove duplicates in list
        serial_list = list(set(serial_list))

        # Check if list is large enough for bulk limits
        if len(serial_list) > self.bulk_query_trigger:
            # Bulk query mode
            self.debug("Device list %s qualifies for bulk query" %
                       len(serial_list))
            self.debug("Getting all devices")

            devices = self.get_all_devices(pagesize=999999)

            # Generate two lists
            # One for serials
            # and one with serial as key for device ID
            self.info("Generating bulk serial list")
            console_serials = []
            console_ids = {}
            for device in devices["Devices"]:
                console_serials.append(device["SerialNumber"])
                console_ids[device["SerialNumber"]] = device["Id"]["Value"]

            # Check through the submitted device list
            for serial in serial_list:
                if str(serial) in console_serials:
                    self.info('Device %s is valid' % serial)
                else:
                    self.warning('Device %s doesn\'t exist' % serial)
                    continue

                device = {}
                device['Id'] = console_ids[str(serial)]
                payload['DeviceAdditions'].append(device)

        else:
            # Small mode, query each device individually
            for serial in serial_list:
                device_response = self.get_device(serial_number=serial)
                if device_response is not False:
                    self.info('Device %s is valid' % serial)
                elif device_response is False:
                    self.warning('Device %s doesn\'t exist' % serial)
                    continue

                device = {}
                device['Id'] = device_response['Id']['Value']
                device['Name'] = device_response['DeviceFriendlyName']
                payload['DeviceAdditions'].append(device)

        if payload['DeviceAdditions'] == []:
            self.error('No devices added to group %s' % group_name)
            return False

        return payload

    def format_group_payload_ogs(self, group_name, og_list):
        """Take a list of OGs and format it for a group POST req"""
        # TODO add bulk limit
        self.info("args: %s" % self.filter_locals(locals()))

        payload = {}
        payload['Name'] = group_name
        payload['CriteriaType'] = 'All'
        payload['OrganizationGroups'] = []

        # Remove duplicates in list
        og_list = list(set(og_list))

        for org_group in og_list:
            og_response = self.find_og(name=org_group)

            if og_response["OrganizationGroups"] == []:
                self.warning("OG %s doesn\'t exist" % org_group)
                continue
            else:
                self.info('OG %s is valid' % org_group)

            og_payload = {}
            og_payload['Id'] = og_response['OrganizationGroups'][0]['Id']
            og_payload['Name'] = og_response['OrganizationGroups'][0]['Name']
            og_payload['Uuid'] = og_response['OrganizationGroups'][0]['Uuid']
            payload['OrganizationGroups'].append(og_payload)

        if payload['OrganizationGroups'] == []:
            self.error("No OGs added to group %s" % group_name)
            return False

        return payload

    def delete_group(self, group_id):
        """Delete a group based on ID"""
        self.info("args: %s" % self.filter_locals(locals()))

        group_name = self.get_group_name(group_id)
        if group_name is None:
            self.error("Group %s doesn't exist" % group_id)
        else:
            self.debug("Deleting group %s" % group_name)
            response = self.rest_v1.delete('/api/mdm/smartgroups/%i' %
                                           group_id)
            self.info(response.text)

            if self.check_http_response(response):
                self.debug("Group %s deleted" % group_name)
                return True
            else:
                self.error("Unable to delete %s" % group_name)
        return False

    def get_all_tags(self, org_group=None, pagesize=500, page=0):
        """Get all tags"""
        return self.find_tag(name=None,
                             org_group=org_group,
                             pagesize=pagesize,
                             page=page)

    def find_tag(self, name=None, org_group=None, pagesize=500, page=0):
        """Gets tags, supports all or searching, returns json"""
        self.info("args: %s" % self.filter_locals(locals()))

        if org_group is None:
            # Set the product to be at the highest OG
            org_group = self.find_og(pagesize=1)['OrganizationGroups'][0]['Id']

        querystring = self.querystring(name=name,
                                       OrganizationGroupId=org_group,
                                       pagesize=pagesize,
                                       page=page)

        response = self.rest_v1.get("/api/mdm/tags/search", querystring)

        if self.check_http_response(response):
            response = json.loads(response.text)['Tags']

            return response

        return False  # pragma: no cover

    def add_tag(self, tag_id: int, devices: list):
        """Adds tags to device list, returns bool"""
        return self.x_tag('add', tag_id, devices)

    def remove_tag(self, tag_id: int, devices: list):
        """Removes tags from device list, returns bool"""
        return self.x_tag('remove', tag_id, devices)

    def x_tag(self, action, tag_id: int, devices: list):
        """Performs an action on device tags"""
        self.info("args: %s" % self.filter_locals(locals()))

        if action not in ['add', 'remove']:
            self.error('%s invalid action')
            return False

        payload = {}
        payload['BulkValues'] = {}
        payload['BulkValues']['Value'] = devices

        response = self.rest_v1.post('/api/mdm/tags/%i/%sdevices' %
                                     (tag_id, action),
                                     json=payload)

        return self.check_http_response(response)

    def get_tagged_devices(self, tag_id: int):
        """Get all devices tagged with tag provided"""
        self.info("args: %s" % self.filter_locals(locals()))

        response = self.simple_get('/api/mdm/tags/%i/devices' % tag_id)

        if response:
            return response['Device']
        else:
            return False  # pragma: no cover

    def create_tag(self, tagname: str, org_group=None, tagtype=1):
        """Create a tag"""
        self.info("args: %s" % self.filter_locals(locals()))

        existing_tag = self.find_tag(name=tagname)
        if existing_tag:
            self.warning('Tag already exists: %s' %
                         existing_tag[0]['Id']['Value'])
            return existing_tag[0]['Id']['Value']

        payload = {}

        if org_group is None:
            # Set the tag to be at the highest OG
            payload['LocationGroupId'] = self.find_og(
                pagesize=1)['OrganizationGroups'][0]['Id']

        payload['TagName'] = tagname
        payload['TagType'] = tagtype

        response = self.rest_v1.post("/api/mdm/tags/addtag", json=payload)

        if self.check_http_response(response):
            return json.loads(response.text)['Value']

        return False  # pragma: no cover

    def delete_tag(self, tagid: int):
        """Delete a tag"""
        self.info("args: %s" % self.filter_locals(locals()))

        response = self.rest_v1.delete('/api/mdm/tags/%i' % tagid)
        return self.check_http_response(response)

    def get_printer(self, printerid: int):  # pragma: no cover
        """Get a printer by ID"""
        # There are no printers available for testing against
        self.info("args: %s" % self.filter_locals(locals()))

        return self.simple_get('/api/mdm/peripherals/printer/%i' % printerid)

    def move_og(self,
                og_id: int,
                macaddress=None,
                udid=None,
                serial_number=None,
                imei=None):
        """Move device in another OG"""
        self.info("args: %s" % self.filter_locals(locals()))

        # Map ids against the WSO format
        ids = {}
        ids["Macaddress"] = macaddress
        ids["Udid"] = udid
        ids["Serialnumber"] = serial_number
        ids["ImeiNumber"] = imei

        _id = None

        for _query in ids:
            if ids[_query] is not None:
                _id = _query
                break

        if _id is None:
            self.error("No device search parameters speficied")
            return False

        self.info("Searching by %s for %s" % (_id, ids[_id]))
        querystring = self.querystring(searchBy=_id, id=ids[_id], ogid=og_id)

        response = self.rest_v1.post(
            '/api/mdm/devices/commands/changeorganizationgroup',
            querystring=querystring)

        return self.check_http_response(response)

    def format_og_payload(self,
                          name: str,
                          group_id: str,
                          location_group_type,
                          country=None,
                          locale=None,
                          default_location=None,
                          devices=None,
                          timezone=None,
                          enable_api=None):
        """Create the payload for a new OG"""

        payload = {}
        # TODO Add value checking, waiting for ticket #20114981204
        # TODO Add country check
        # TODO refactor the checking for blank vars
        # TODO Check timezone ID

        location_group_types = [
            "Container", "Division", "Prospect", "Region", "UserDefined"
        ]
        if location_group_type in location_group_types:
            payload["LocationGroupType"] = location_group_type

        if not self.utils.check_timezone(timezone):
            self.error("Invalid timezone %s for %s" % (name, timezone))
            return False

        if not self.utils.check_locale(locale):
            self.error("Invalid locale %s for %s" % (name, locale))
            return False

        payload["Name"] = name
        payload["GroupId"] = group_id
        if country:
            payload["Country"] = country
        if locale:
            payload["Locale"] = locale
        if default_location:
            payload["AddDefaultLocation"] = default_location
        if devices:
            payload["Devices"] = devices
        if enable_api:
            payload["EnableRestApiAccess"] = enable_api
        if timezone:
            payload["Timezone"] = timezone

        self.debug(payload)

        return payload

    def create_og(self,
                  parentog_id: int,
                  payload=dict,
                  strict_name=True,
                  strict_group_id=True):
        """Create OG using payload"""
        # Note that the name does not need to be unique for the API
        # Group ID has to be unique but there is no way to search by group ID
        # except to load all OGs and seach through all OGS
        # to increase performance you can disable this
        if strict_name and self.find_og(
                name=payload["Name"])["OrganizationGroups"]:
            self.error("OG %s already exists, unable to create" %
                       payload["Name"])
            return False

        if strict_group_id:
            if payload["GroupId"] != "":
                ogs = self.get_all_ogs(pagesize=99999)['OrganizationGroups']
                for og in ogs:
                    if payload["GroupId"] == og['GroupId']:
                        self.error(
                            "OG with groupId %s already exists, unable to create"
                            % payload["Name"])
                        return False

        response = self.rest_v2.post("/api/system/groups/%i" % parentog_id,
                                     json=payload)

        if self.check_http_response(response):
            return self.str_to_json(response.text)

        return False

    def delete_og(self, og_uuid):
        """Delete an OG using the UUID"""
        self.info("Deleting OG %s" % og_uuid)

        response = self.rest_v2.delete("/api/system/groups/%s" % og_uuid)

        return self.check_http_response(response)

    def reprocess_product(self, product_id, device_list, force=True):
        """Reprocess a product"""
        self.info("args: %s" % self.filter_locals(locals()))

        payload = {}
        payload['ForceFlag'] = force

        device_ids = []
        if device_list:
            for device in device_list:
                device_payload = {}
                device_payload['ID'] = device
                device_ids.append(device_payload)

        payload['DeviceIds'] = device_ids
        payload['ProductID'] = product_id

        response = self.rest_v1.post('/api/mdm/products/reprocessProduct',
                                     json=payload)

        return self.check_http_response(response)

    def create_product(self,
                       name,
                       description,
                       action_type_id,
                       action_item_id,
                       platform_id,
                       managed_by_og=None):
        """Creates a product using fileId, actionType.
         Product will be inactive and has no assigned groups. Returns int of new ID"""
        self.info("args: %s" % self.filter_locals(locals()))

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
        if managed_by_og is None:
            payload['ManagedByOrganizationGroupID'] = self.find_og(
                pagesize=1)["OrganizationGroups"][0]["Id"]
        else:
            payload['ManagedByOrganizationGroupID'] = managed_by_og
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

        self.debug("Create product: %s" % payload)

        product_name = self.find_product(name)

        if not product_name:
            self.debug("Product %s does not exist" % name)

            response = self.rest_v1.post('/api/mdm/products/create', json=payload)

            if self.check_http_response(response):
                return self.str_to_json(response.text)['Value']
            else:
                self.error("Unable to create product %s" % product_name)

        else:
            self.error("Product %s already exists, unable to create" %
                       product_name)
            return False

    def get_user(self,
                 firstname=None,
                 lastname=None,
                 email=None,
                 locationgroupId=None,
                 role=None,
                 username=None,
                 status=None,
                 pagesize=500,
                 page=0):
        """Search for a user"""
        self.info("args: %s" % self.filter_locals(locals()))

        if status:
            if status not in ("Active", "Inactive"):
                self.error("Invalid user status parameter")
                return False

        # Set base URL
        url = '/api/system/users/search'

        # Map ids against the WSO format
        ids = {}
        ids["firstname"] = firstname
        ids["lastname"] = lastname
        ids["email"] = email
        ids["locationgroupId"] = locationgroupId
        ids["role"] = role
        ids["username"] = username
        ids["status"] = status

        _id = None

        for _query in ids:
            if ids[_query] is not None:
                _id = _query
                break

        if _id is None:
            self.error("No User search parameters speficied")
            return False

        self.info("Searching by %s for %s" % (_id, ids[_id]))
        querystring = self.querystring(searchBy=_id,
                                       id=ids[_id],
                                       pagesize=pagesize,
                                       page=page)

        return self.simple_get(url, querystring, 1)

    def change_user(self, device_id=int, user_id=int):
        """Change the enrolment user for a device"""
        response = self.rest_v2.patch(
            '/api/mdm/devices/%s/enrollmentuser/%s' % (device_id, user_id), "")

        return self.check_http_response(response)

    # TODO Add Bulk commands

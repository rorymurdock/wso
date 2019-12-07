"""WSO UEM package for managing large WSO instances"""
import sys
import json
import time
import logging

from basic_auth import Auth
from reqrest import REST


class WSO():
    """WSO API facade"""
    def __init__(self, config="config", debug=True):

        # Sort out logging
        log_level = logging.INFO
        if debug:
            log_level = logging.INFO
            # TODO: Change back to error

        logging.basicConfig(filename='app.log',
                            filemode='w',
                            format='%(levelname)s\t%(funcName)s\t%(message)s',
                            level=log_level)

        # Create logging functions
        self.debug = logging.debug
        self.info = logging.info
        self.warning = logging.warning
        self.error = logging.error
        self.critical = logging.critical

        # Set max size line to log
        self.max_log = 9000

        # Get config
        self.config = Auth(config).read_config("uem.json")

        if not self.config:
            self.critical("Unable to get config, run configure.py")
            sys.exit(1)

        self.info("Imported config - %s" % self.config)

        # Create v1 API object
        headers_v1 = self.create_headers(version=1)

        self.rest_v1 = REST(url=self.config['url'],
                            headers=headers_v1,
                            proxy=self.import_proxy(),
                            debug=debug)

        # Create v2 API object
        headers_v2 = self.create_headers(version=2)

        self.rest_v2 = REST(url=self.config['url'],
                            headers=headers_v2,
                            proxy=self.import_proxy(),
                            debug=debug)

    def create_headers(self, version=2):
        """Creates headers for REST API Call using config and version"""
        headers = {
            'Accept': "application/json;version=%s" % version,
            'aw-tenant-code': self.config['aw-tenant-code'],
            'Authorization': self.config['authorization'],
            'Content-Type': "application/json"
        }

        self.info("Generated v%i headers - %s" % (version, headers))

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
        status_codes[406] = True, 'HTTP 406: Not Acceptable'
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

        for _item in _list:
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

        else:
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

        return self.simple_get(url, querystring, 1)

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
        self.info("args: %s" % self.filter_locals(locals()))
        # Set base URL
        url = '/api/mdm/smartgroups/%i' % group_id

        # Add arguments
        querystring = self.querystring(pagesize=pagesize, page=page)

        return self.simple_get(url, querystring, 1)

    def find_group(self, name=None, pagesize=500, page=0):
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
        url = '/api/mdm/products/%i' % product_id

        # Add arguments
        querystring = self.querystring(pagesize=pagesize, page=page)

        return self.simple_get(url, querystring, 1)

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

        response = self.simple_get(url, version=1)

        if response:
            self.info("%s has been %sd" % (product['Name'], action))

        return response

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
            self.critical("Product has groups assigned, unable to delete" %
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

        # TODO: Validate all parameters

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
            print("No device search parameters speficied")
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

        # TODO: Validate all parameters

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
            print("No device search parameters speficied")
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

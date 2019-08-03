import re
import json
from reqREST import REST

with open('config/uem.json') as json_file:
    url = json.load(json_file)['url']

# Create REST instance
rest = REST(url=url)

# At some stage the version file changed, try both
urls = ['/api/help/local.json', '/api/system/help/localjson']

# Try the first URL
response = rest.get(urls[0])

# If that 404's try the second URL
if response.status_code == 404:
    response = rest.get(urls[1])

# If this 200 OKs
if response.status_code == 200:
    # Get the text, parse is
    versions = json.loads(response.text)
    version = versions['apis'][0]['products'][0]

    # Regex it to remove AirWatch and VMWare Workspace ONE UEM strings
    # Leaving just the version number
    version = re.match(
        r'(AirWatch|VMware Workspace ONE UEM);(.*)',
        version,
        re.M|re.I
        ).group(2)

# 403 forbidden, API help page must be protected
elif response.status_code == 403:
    version  = 'API Protected'

print('Using WSO UEM Version %s' % version)

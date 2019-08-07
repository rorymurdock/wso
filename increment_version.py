import re
import os

# Open setup fule
f = open("setup.py", "r")

for line in f:
    # Find the version line
    if "version=" in line:

        # Regex the old version out
        version = re.match(r'(.*)version=\"(\d).(\d).(\d)\"',line,re.M|re.I)

        # Assign individually so we can increment the micro
        major = int(version.group(2))
        minor = int(version.group(3))
        micro = int(version.group(4))

old_version = "%i.%i.%i" % (major, minor, micro)
new_version = "%i.%i.%i" % (major, minor, micro+1)

print("Old version: %s" % old_version)
print("Incrementing to %s" % new_version)

# Sed / replace any instances of old version with the new version
if os.system("sed -i 's/%s/%s/g' setup.py" % (old_version, new_version)):
    print("Version update successfully")

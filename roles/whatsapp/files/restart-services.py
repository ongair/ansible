#!/usr/bin/python

import os
import re

conf = os.path.dirname("/etc/init/")

ongair_service_format = r'^(ongair-.+)\.conf$'
ongair_confs = list(
    filter((lambda file: re.search(ongair_service_format, file)),
           os.listdir(conf)))

services = []
for item in ongair_confs:
    match = re.search(ongair_service_format, item)
    if match:
        service = match.group(1)
        services.append(service)
        os.system("sudo service restart %s" % (service))
    else:
        print("Not an ongair service")

print(ongair_confs)
print(services)

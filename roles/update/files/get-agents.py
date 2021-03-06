#!/usr/bin/python

import os
import re

conf = os.path.dirname("/etc/init/")

ongair_service_format = r'^(ongair-.+)\.conf$'
ongair_confs = list(
    filter((lambda file: re.search(ongair_service_format, file)),
           os.listdir(conf)))

agents = []
for item in ongair_confs:
    match = re.search(ongair_service_format, item)
    if match:
        service = match.group(1)
        agents.append(service)

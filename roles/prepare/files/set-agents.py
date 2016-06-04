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

# fact file
path = "/etc/ansible/facts.d/agents.fact"
file = open(path, 'w')

print "Writing to facts file %s" %path

file.write("{\n")
accounts = ", ".join("\"%s\"" %x.split('ongair-')[1] for x in agents)
file.write("\t\"account\": [%s]\n}\n" %accounts)
file.close()

print "Finished agents"
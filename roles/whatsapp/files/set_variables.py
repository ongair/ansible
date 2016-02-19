#!/usr/bin/python


import os
import yaml

variables_file = os.path.join('/opt/','variables.yml')

variables = yaml.load(open(variables_file, 'r'))
for key, value in variables.iteritems():
    print(key)
    print(value)
    os.environ[key] = value


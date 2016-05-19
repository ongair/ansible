import os
import sys
import json
import time
from collections import defaultdict

import boto3

from flask import Flask
from flask import jsonify


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SSH_DIR = os.path.abspath("~/.ssh/")
# AVAILABILITY_ZONE = 'ap-southeast-1'
AVAILABILITY_ZONE = 'eu-west-1'
INSTANCE_TYPE = 't1.micro'
KEY_PAIR_NAME = 'ongair-shared'
KEY_PAIR_ID = 'xxxyyx'
SUBNET_ID = 'string'
VPC_ID = 'string'
SECURITY_GROUP = 'ongair-default'
SECURITY_GROUP_ID = 'sg-a05abac7'
BASE_IMAGE_ID = 'ami-a2d145d1' #This is the ongair image with configuration done.
# BASE_IMAGE_ID = 'ami-3832e45b' #This is the ongair image with configuration done.

app = Flask(__name__)

client = boto3.client('ec2')

ec2 = boto3.resource('ec2')


def launch_instance(phonenumber, tag=None):
    """
    creates a new ongair instance and returns the instance details
    """
    try:
        name = "Ongair-%s" % (phonenumber) if tag is None else tag
        client = boto3.client('ec2')
        instance = client.run_instances(
            ImageId=BASE_IMAGE_ID,
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_PAIR_NAME,  # Should be a get or create key.
            SecurityGroupIds=[
                SECURITY_GROUP_ID,
            ],
            InstanceType='t2.micro',
            Placement={
                'AvailabilityZone': AVAILABILITY_ZONE,
                # 'GroupName': 'whatsapp-agents', #Get or create group name
                'Tenancy': 'default',

            },

            Monitoring={
                'Enabled': True
            },

            InstanceInitiatedShutdownBehavior='terminate',  # Should be stop,

        )

        instance_id = instance['Instances'][0]['InstanceId']

        # Tag the instance
        tags = client.create_tags(
            Resources=[instance_id],
            Tags=[{
                'Key': 'Name',
                'Value': name
            },
                {
                'Key': 'Number',
                'Value': phonenumber
            },
                {
                'Key': 'instance-purpose',
                'Value': 'whatsapp-agent'
            },
                {
                'Key': 'env',
                'Value': 'production'
            }])
        this_instance = client.describe_instances(InstanceIds=[instance_id])

        while this_instance['Reservations'][0]['Instances'][0]['State']['Name'] != 'running':
            time.sleep(5)
            this_instance = client.describe_instances(InstanceIds=[instance_id])
            print "Instance state: %s" % this_instance['Reservations'][0]['Instances'][0]['State']['Name']

        # print this_insta   nce

        instance = this_instance['Reservations'][0]['Instances'][0]

        details = {
            'tags': instance.get('Tags'),
            'key_name': instance.get('KeyName'),
            'state': instance.get('State'),
            'launch_time': instance.get('LaunchTime'),
            'public_ip_address': instance.get('PublicIpAddress'),
            'private_ip_address': instance.get('PrivateIpAddress'),
            'public_dns_name': instance.get('PublicDnsName'),
            'instance_type': instance.get('InstanceType'),
            'image_id': instance.get('ImageId'),
            'instance_id': instance.get('InstanceId'),
            'network_interfaces': instance.get('NetworkInterfaces')
        }

        return details
    except:
        # print 'Error'
        print "Unexpected error:", sys.exc_info()
        return []


def stop_instance(id):
    # ec2.instances.filter(InstanceIds=[id]).stop()
    response = client.stop_instances(InstanceIds=[id])
    print response
    return response['StoppingInstances'][0]


def restart_instance(id):
    response = client.reboot_instances(InstanceIds=[id])
    print response
    return response


def create_key_pair():
    """
    Creates a key pair if one doesn't exist and stores in a local ssh directory.
    Ongair whatsapp agents have a shared key pair.
    """
    key_name = KEY_PAIR_NAME
    file_name = "%s.pem" % (key_name)
    file_path = os.path.join(os.path.abspath(SSH_DIR), file_name)
    print file_path

    if not os.path.exists(file_path):
        key_pair = client.create_key_pair(KeyName=key_name)
        key = key_pair['KeyMaterial']
        try:
            with open(file_path, "w+") as f:
                f.write(key)
        except IOError, e:
            print("cant write file")
    return file_path


def get_ip_addresses():
    ec2 = client.describe_instances()
    addresses = client.describe_addresses()
    return jsonify(**addresses)


def list_agents():
    ec2 = boto3.resource('ec2')
    active_filter = { 'Name': 'instance-state-name', 'Values': ['running']}
    purpose_filter = { 'Name': 'tag:instance-purpose', 'Values': ['whatsapp-agent'] }

    filters = [active_filter, purpose_filter]

    running_instances = ec2.instances.filter(Filters=filters)

    details = defaultdict()

    servers = {
        'count': 0,
        'instances': []
    }

    for instance in running_instances:
        print instance.id
        tags = instance.tags
        instance_name = None
        if tags:
            for tag in tags:
                if 'Name' in tag['Key']:
                    instance_name = tag['Value']

        details = {
            'instance_id': instance.id,
            'instance_name': instance_name,
            'instance_type': instance.instance_type,
            'state': instance.state['Name'],
            'private_ip': instance.private_ip_address,
            'public_ip': instance.public_ip_address,
            'launch_time': instance.launch_time,
            'image_id': instance.image_id,
            'public_dns_name': instance.public_dns_name,
            'key_name': instance.key_name
        }

        servers['instances'].append(details)
        servers['count'] += 1
    return servers

import os
import json
import time
from collections import defaultdict

import boto3

from flask import Flask
from flask import jsonify


BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SSH_DIR = os.path.abspath("/home/james/.ssh/")
AVAILABILITY_ZONE = 'eu-west-1b'
INSTANCE_TYPE = 't1.micro'
KEY_PAIR_NAME = 'ongair-shared'
KEY_PAIR_ID = 'xxxyyx'
SUBNET_ID = 'string'
VPC_ID = 'string'
SECURITY_GROUP = 'ongair-default'
SECURITY_GROUP_ID = 'sg-a05abac7'
BASE_IMAGE_ID = 'ami-b0c379c3'

app = Flask(__name__)

client = boto3.client('ec2')

ec2 = boto3.resource('ec2')


def launch_instance(phonenumber):
    """
    creates a new ongair instance and returns the instance details
    """
    name = "Ongair-%s" % (phonenumber)
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
        }])
    this_instance = client.describe_instances(InstanceIds=[instance_id])

    while this_instance['Reservations'][0]['Instances'][0]['State']['Name'] != 'running':
        time.sleep(5)
        this_instance = client.describe_instances(InstanceIds=[instance_id])
        print "Instance state: %s" % this_instance['Reservations'][0]['Instances'][0]['State']['Name']

    # print this_instance

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


def stop_instance(id):
    ec2.instances.filter(InstanceIds=[id]).stop()


def restart_instance(id):
    ec2.instances.filter(InstanceIds=[id]).restart()


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
    running_instances = ec2.instances.filter(Filters=[{
        'Name': 'instance-state-name',
        'Values': ['running']}])

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
    return jsonify(**servers)

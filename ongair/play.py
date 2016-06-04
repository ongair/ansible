import os
import json
import time

from collections import defaultdict
from tempfile import NamedTemporaryFile


import boto3
import jinja2

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response
from flask import jsonify
from flask_restful import reqparse

from ansible.playbook import PlayBook
from ansible.inventory import Inventory, host, group
from ansible.runner import Runner
from ansible import callbacks
from ansible import utils
import ansible.constants as C

from aws.ec2 import launch_instance, list_agents, get_ip_addresses, stop_instance, restart_instance
from setup.playbooks import prepare, add_to_server, update_agents

app = Flask(__name__)
C.HOST_KEY_CHECKING = False

inventory = """deploy_user: {{deploy_user}}
agents:
       - { account_number: {{number}}, agent_name: {{agent_name}} }
"""

TRIAL_HOST = '52.50.138.0' #This is the current trial server and can change


# Boilerplace callbacks for stdout/stderr and log output
utils.VERBOSITY = 0
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
stats = callbacks.AggregateStats()
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)


@app.route('/list')
def index():
    agents = list_agents()
    return jsonify(agents)


@app.route('/ips')
def ips():
    public_ips = get_ip_addresses()
    return public_ips

@app.route('/stop')
def stop():
    if not 'instanceid' in request.args:
        message = 'Please send request to stop instance in this format: /stop?instanceid=<instanceid>'
        data = {
            'status': 400,
            'message': message
        }
        js = json.dumps(data)

        resp = Response(js, status=400, mimetype='application/json')

        return resp
    else:
        instanceid = request.args['instanceid']

    response = stop_instance(instanceid)
    js = json.dumps(response)
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route('/restart')
def restart():
    if not 'instanceid' in request.args:
        message = 'Please send request to stop instance in this format: /restart?instanceid=<instanceid>'
        data = {
            'status': 400,
            'message': message
        }
        js = json.dumps(data)

        resp = Response(js, status=400, mimetype='application/json')

        return resp
    else:
        instanceid = request.args['instanceid']

    response = restart_instance(instanceid)
    data = {
        "message": "Rebooting Instance",
        "status": 200,
        "response": response,
        "instanceid": instanceid
    }
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route('/prepare', methods=['POST', 'GET'])
def prep():
    ip = request.args['ip']
    start = time.time()

    result = prepare(ip)
    print 'Results: %s' %result

    duration = round(time.time() - start, 2)
    return jsonify(time_taken=duration, success=result, message='success', status=200)


@app.route('/update',  methods=['POST'])
def update_servers():
    start = time.time()
    # limit = request.form['limit']
    parser = reqparse.RequestParser()
    parser.add_argument('limit')
    args = parser.parse_args()

    limit = args['limit']

    servers = list_agents()
    ips = [ server['public_ip'] for server in servers['instances'] ]
    if limit is not None:
        ips = [ ip for ip in ips if ip == limit ]        

    if len(ips) > 0:
        update_agents(ips)


    return jsonify(success=True, ips=ips, limit=limit)

@app.route('/provision')
def provision():
    start = time.time()
    number = request.args['number']
    ip = request.args['ip']

    result = add_to_server(ip, number)
    duration = round(time.time() - start, 2)
    print 'Provisioned %s' %number

    return jsonify(time_taken=("%s seconds" % duration), success=result, number=number, message=("successfully added %s to %s" % (number, ip)), status=200)

@app.route('/trial')
def trial():
    start = time.time()
    if not 'number' in request.args:
        message = 'Please send the request with a trial this format: /trial?number=<number>'
        data = {
            'status': 400,
            'message': message
        }
        js = json.dumps(data)

        resp = Response(js, status=400, mimetype='application/json')

        return resp
    else:
        number = request.args['number']

    agent_name = 'ongair-%s' % (number)

    trial_host = host.Host(name=TRIAL_HOST, port=22)
    trial_host.set_variable('deploy_user', 'ubuntu')
    trial_host.set_variable('account_number', number)
    trial_host.set_variable('agent_name', 'ongair-%s' % (number))
    trial_host.set_variable('public_ip_address', TRIAL_HOST)
    trial_host.set_variable(
        'project_directory', '/home/deploy/apps/whatsapp/')
    trial_host.set_variable(
        'virtualenv_directory', '/home/deploy/apps/whatsapp/venv/')
    # secondly set up the group where the host(s) has to be added
    host_group = group.Group(
        name='trial'
    )
    host_group.add_host(trial_host)

    # the next step is to set up the inventory itself
    trial_inventory = Inventory([])
    trial_inventory.add_group(host_group)
    vault_password_file_path = os.path.expanduser("~/.vault_pass.txt")
    vault_password_file = open(vault_password_file_path, "rw+")

    playbook = os.path.join(os.path.abspath('..'), 'add-to-trial.yml')

    # Now we run our playbook
    pb = PlayBook(
        playbook=playbook,
        inventory=trial_inventory,
        remote_user='ubuntu',
        remote_port=22,
        private_key_file='~/.ssh/ongair-shared.pem',
        # private_key_file='~/.ssh/ongair-whatsapp-key.pem',
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        vault_password=vault_password_file.read().split()[0]

    )

    try:

        results = pb.run()

    except Exception, e:
        print e

    # Ensure on_stats callback is called
    # for callback modules
    playbook_cb.on_stats(pb.stats)
    end = time.time()
    time_taken = end - start
    data = {
        "message": "successfully added %s to trial" % (number),
        "status": 200,
        # "data": results,
        "number": number,
        "agent_name": agent_name,
        "time_taken": "%s seconds" % round(time_taken, 2)
    }
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    # notifyslack(number)
    return resp


@app.route('/production')
def production():
    """
    launch an ec2 production instance.
    Add the account number to the ec2 instance via the deploy module.
    return the ec2 instance details and the new account number
    that has been added.

    """

    if not 'number' in request.args:
        return jsonify(success=False, message='Number parameter is required')
    else:
        # Start the timer to measure how much time the request takes
        start = time.time()

        # Get the number and name from request
        number = request.args['number']
        name = request.args['name'] if 'name' in request.args else None

        print('About to create instance for %s tagged %s' %(number, name))

        # # Now we launch the new production instance
        # # We pass the number for tagging and naming of the instance
        new_production_host = launch_instance(number, name)
        hostname = new_production_host.get('public_ip_address')
        
        print("New instance with ip %s is now ready for prep" %hostname)
        ready = prepare(hostname)
        print "Results: %s" %ready

        result = ready

        if ready:
            result = add_to_server(hostname, number)

        print 'Completed setup. Result is %s' %result
        
        time_taken = round(time.time() - start, 2)        
        return jsonify(time_taken=time_taken, success=result, message='success', status=200, number=number, hostname=hostname)



if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

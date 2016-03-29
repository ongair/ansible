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

from ansible.playbook import PlayBook
from ansible.inventory import Inventory, host, group
from ansible.runner import Runner
from ansible import callbacks
from ansible import utils

from utils.slack import notifyslack

app = Flask(__name__)

inventory = """deploy_user:{{ deploy_user }}
agents:
       - { account_number: {{number}}, agent_name: {{agent_name}} }
"""


# Boilerplace callbacks for stdout/stderr and log output
utils.VERBOSITY = 0
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
stats = callbacks.AggregateStats()
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)


@app.route('/')
def index():
    return "<h1 style='color:blue'>Welcome!</h1>"


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

    inventory_template = jinja2.Template(inventory)
    rendered_inventory = inventory_template.render({
        'deploy_user': 'ubuntu',
        'number': number,
        'agent_name': 'ongair-%s' % (number)
    })
    file_path = os.path.join(os.path.abspath('..'), 'group_vars/ongair-ec2')
    playbook_path = os.path.join(os.path.abspath('..'), 'add-to-trial.yml')
    inventory_path = os.path.join(os.path.abspath('..'), 'trial')
    print(inventory_path)
    try:
        with open(file_path, "w+") as f:
            f.write(rendered_inventory)
    except IOError, e:
        print("cant write to file")

    vault_password_file_path = os.path.expanduser("~/.vault_pass.txt")

    vault_password_file = open(vault_password_file_path, "rw+")

    pb = PlayBook(
        playbook=playbook_path,
        remote_user='ubuntu',
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        remote_port=22,
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
        "data": results,
        "time_taken": round(time_taken, 2)
    }
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    notifyslack(number)
    return resp


@app.route('/production')
def production():
    """
    launch ec2 instance.
    Add this number to the ec2 instance via the deploy module.
    return the ec2 instance details and the new account number 
    that has been added.

    """
    start = time.time()
    number = '0000001111110000001111'

    # first of all, set up a host (or more)
    ongair_host = host.Host(
        name='54.229.173.120',
        port=22
    )
    # with its variables to modify the playbook
    ongair_host.set_variable('deploy_user', 'ubuntu')
    ongair_host.set_variable('account_number', number)
    ongair_host.set_variable('agent_name', 'ongair-%s' % (number))
    ongair_host.set_variable('project_directory', '/home/deploy/apps/whatsapp/')
    ongair_host.set_variable('virtualenv_directory', '/home/deploy/apps/whatsapp/venv/')

    print(ongair_host.vars)

    # secondly set up the group where the host(s) has to be added
    host_group = group.Group(
        name='whatsapp'
    )
    host_group.add_host(ongair_host)

    # the last step is set up the inventory itself
    ongair_inventory = Inventory([])
    ongair_inventory.add_group(host_group)
    # ongair_inventory.get_group('whatsapp').add_host(ongair_host)

    print(ongair_inventory)


    production_playbook = os.path.join(os.path.abspath('..'), 'production.yml')
    print(production_playbook)
    vault_password_file_path = os.path.expanduser("~/.vault_pass.txt")
    vault_password_file = open(vault_password_file_path, "rw+")

    pb = PlayBook(
        playbook=production_playbook,
        inventory=ongair_inventory,
        remote_user='ubuntu',
        remote_port=22,
        private_key_file='~/.ssh/ongair-whatsapp-key.pem',
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        vault_password=vault_password_file.read().split()[0]

    )
    print(pb.playbook)
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
        "message": "success",
        "status": 200,
        "data": results,
        "time_taken": round(time_taken, 2)
    }
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    # notifyslack(number)
    return resp


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

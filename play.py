import os
import json
import time
from collections import defaultdict
from tempfile import NamedTemporaryFile


import boto3
import jinja2

from flask import Flask
from flask import jsonify
from ansible.playbook import PlayBook
from ansible.inventory import Inventory
from ansible import callbacks
from ansible import utils

app = Flask(__name__)

inventory = """
deploy_user: {{deploy_user}}
agents:
       - { account_number: {{number}}, agent_name: {{agent_name}} }
"""


# Boilerplace callbacks for stdout/stderr and log output
utils.VERBOSITY = 0
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
stats = callbacks.AggregateStats()
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)


# @app.route('add-number/<number>')
@app.route('/trial/<number>')
def trial(number):
    # number = number
    inventory_template = jinja2.Template(inventory)
    rendered_inventory = inventory_template.render({
    'deploy_user': 'ubuntu',
    'number': number,
    'agent_name': 'ongair-%s' % (number)
    })
    print(rendered_inventory)
    file_path = os.path.join(os.path.abspath('group_vars'), 'ongair-ec2')
    print(file_path)
    try:
        with open(file_path, "w+") as f:
            f.write(rendered_inventory)
    except IOError, e:
        print("cant write to file")
    # hosts = NamedTemporaryFile(delete=False)
    # hosts.write(rendered_inventory)
    # host.name = 'ongair-ec2'
    # hosts.close()
    pb = PlayBook(
        playbook='add-to-trial.yml',
        # host_list=hosts.name,
        # inventory=hosts.name,     # Our hosts, the rendered inventory file
        remote_user='ubuntu',
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        vault_password='whts@99Ongair-3#ncrypt!2@16',                                    
        private_key_file='~/.ssh/ongair-whatsapp-key.pem'
    )
    results = pb.run()
    # Ensure on_stats callback is called
    # for callback modules
    playbook_cb.on_stats(pb.stats)
    print results



    return jsonify(results)


if __name__ == '__main__':
    app.debug = True
    app.run()

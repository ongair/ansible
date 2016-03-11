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


@app.route('add-number/<number>')
def trial():
	inventory_template = jinja2.Template(inventory)
	rendered_inventory = inventory_template.render({
    'deploy_user': 'ubuntu',
    'number': number,
    'agent_name': 'ongair-%s' % (number)
    })

    host = NamedTemporaryFile(delete=False)
    host.write(rendered_inventory)
    host.close()
    pb = PlayBook(
    playbook='deploy.yml',
    host_list='ec2-test',     # Our hosts, the rendered inventory file
    remote_user='ubuntu',
    callbacks=playbook_cb,
    runner_callbacks=runner_cb,
    stats=stats,
    private_key_file='/home/james/.ssh/ongair-whatsapp-key.pem'
    )
    results = pb.run()
    # Ensure on_stats callback is called
    # for callback modules
    playbook_cb.on_stats(pb.stats)
    os.remove(hosts.name)
    print results



    return jsonify('details')


if __name__ == '__main__':
    app.debug = True
    app.run()

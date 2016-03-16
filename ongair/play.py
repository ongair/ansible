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


@app.route('/')
def index():
    return "<h1 style='color:blue'>Welcome!</h1>"



@app.route('/trial', methods=['POST'])
def trial():
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
    file_path = os.path.join(os.path.abspath('./group_vars'), 'ongair-ec2')
    print(file_path)
    try:
        with open(file_path, "w+") as f:
            f.write(rendered_inventory)
    except IOError, e:
        print("cant write to file")

    pb = PlayBook(
        playbook='../add-to-trial.yml',
        remote_user='ubuntu',
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        vault_password=os.environ['ongairvaultpassword'],
    )
    try:
        start = time.time()
        results = pb.run()
        end = time.time()
    except Exception, e:
        print e

    # Ensure on_stats callback is called
    # for callback modules
    playbook_cb.on_stats(pb.stats)
    data = {
        "message": "successfully added %s to trial" % (number),
        "status": 200,
        "data": results,
        "time_taken": end-start
    }
    js = json.dumps(data)
    resp = Response(js, status=200, mimetype='application/json')
    return resp


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

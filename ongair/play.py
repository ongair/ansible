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

inventory = """deploy_user: {{deploy_user}}
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

    pb = PlayBook(
        playbook=playbook_path,
        remote_user='ubuntu',
        callbacks=playbook_cb,
        runner_callbacks=runner_cb,
        stats=stats,
        # inventory=Inventory(['inventory_path']),
        # host_list='inventory_path',
        # vault_password=os.environ['ongairvaultpassword'],
        vault_password='whts@99Ongair-3#ncrypt!2@16'
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
    return resp

def notifyslack(number):
    """
    from slackclient import SlackClient

    token = "xoxp-28192348123947234198234"      # found at https://api.slack.com/web#authentication
    sc = SlackClient(token)
    print sc.api_call("api.test")
    print sc.api_call("channels.info", channel="1234567890")
    print sc.api_call(
        "chat.postMessage", channel="#general", text="Hello from Python! :tada:",
        username='pybot', icon_emoji=':robot_face:'
    )
    """
    return None


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')

import os
import json
import time
from collections import defaultdict

import boto3

from flask import Flask
from flask import jsonify


@app.route('add_number_to_trial/<number>')
def trial():
    return jsonify('details')


if __name__ == '__main__':
    app.debug = True
    app.run()

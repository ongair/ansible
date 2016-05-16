import os
import json

from ansible import utils
from ansible import callbacks
from ansible.playbook import PlayBook
from ansible.inventory import Inventory, host, group

# Standard Variables
PROJECT_DIR = '/home/deploy/apps/whatsapp/'
VENV_DIR = '/home/deploy/apps/whatsapp/venv/'
KEY_FILE = '~/.ssh/ongair-shared.pem'
PASSWD_FILE = '~/.vault_pass.txt'

# Ansible callbacks
utils.VERBOSITY = 0
playbook_cb = callbacks.PlaybookCallbacks(verbose=utils.VERBOSITY)
stats = callbacks.AggregateStats()
runner_cb = callbacks.PlaybookRunnerCallbacks(stats, verbose=utils.VERBOSITY)

def add_to_server(ip, number):
  """
    Add a number to a server
    Already assumes the server is prepared
  """
  agent_name = 'ongair-%s' %number
  result = run_playbook(ip, 'trial', 'add-to-trial.yml', number, agent_name)
  return parse_results(result, ip)


def prepare(ip):
  """
    Prepare a server - 
    runs any configuration that may be missing from the base image
  """
  result = run_playbook(ip, 'targets', 'prepare.yml')
  print 'Finished preparing %s' %result
  return parse_results(result, ip)


def run_playbook(ip, group_name, playbook_file, account_number=None, agent_name=None):
  hst = host.Host(name=ip, port=22)
  hst.set_variable('deploy_user', 'ubuntu')
  hst.set_variable('public_ip_address', ip)
  hst.set_variable('project_directory', PROJECT_DIR)
  hst.set_variable('virtualenv_directory', VENV_DIR)
  hst.set_variable('account_number', account_number)
  hst.set_variable('agent_name', agent_name)

  grp = group.Group(name=group_name)
  grp.add_host(hst)

  inv = Inventory([])
  inv.add_group(grp)
  vault_password_file_path = os.path.expanduser(PASSWD_FILE)
  vault_password_file = open(vault_password_file_path, 'rw+')

  playbook = os.path.join(os.path.abspath('..'), playbook_file)
  pb = PlayBook(
    playbook=playbook,
    inventory=inv,
    remote_user='ubuntu',
    remote_port=22,
    private_key_file=KEY_FILE,
    callbacks=playbook_cb,
    runner_callbacks=runner_cb,
    stats=stats,
    vault_password=vault_password_file.read().split()[0]
  )

  try:
    results = pb.run()
    return results
  except Exception, e:
    print e
    return None

def parse_results(result_hash, ip):
  if result_hash is not None:
    result = result_hash[ip]  
    return result['failures'] == 0
  else:
    return False
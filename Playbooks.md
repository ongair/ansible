## Quick guide to using Ansible for Ongair ##

Read this after going over the Readme.md file in this repository. This outlines the steps for various common activities.

### Setting up a new Trial Server ###
- Create the server in AWS and take note of the IP address.
- Add the new host to the trial inventory file. If you are only setting up the new server replace the old server under the trial:children
  
  ```
    [trial-host-n]
    <ip-address> ansible_ssh_private_key_file=~/.ssh/ongair-shared.pem ansible_ssh_user=ubuntu

    [trial:children]
    trial-host-n
  ``` 

- Run the ansible playbook to setup this server
  ```
    ansible-playbook -i trial setuptrial.yml
  ``` 

- Update the `TRIAL_HOST` variable in `ongair/play.py` to point to the new trial server

- Push to github and Update the API server

### Updating the API server ###

You need to update the provisioning API server to use the new api. The ansible module for doing this is available [here](https://github.com/ongair/ansible-aws).

```
    ansible-playbook -i hosts deploy.yml 
```

### Running the API server in development ###

```
    #activate the virtual environment in the ongair folder
    gunicorn play:app -t 600 --reload
```

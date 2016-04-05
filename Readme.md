# Installation #

You need to install ansible on the control machine

**MacOS**
```
    sudo pip install ansible
```

**Ubuntu**
```
    sudo apt-get install software-properties-common
    sudo apt-add-repository ppa:ansible/ansible
    sudo apt-get update
    sudo apt-get install ansible
```

## Getting Started ##
The code is available [on github](https://github.com/ongair/ansible)

```
git clone git@github.com:ongair/ansible.git && cd ansible
```
### Setup Ansible Vault Encryption Password ###

To securely store the secret data this software uses to configure Ongair-whatsapp servers, we use ansible vault to encrypt the data.  
The first thing we do here is to setup the encryption password that ansible will be using to encrypt and decrypt these variables.

```sh 
echo 'strong password' >> ~/.vault_pass.txt
```
### Encyrpting ongair Secret Variables ###
Once the encryption password is setup, we can now use it to encyrpt files in this folder. The secret variables are stored in the file `roles/whatsapp/vars/variables.yml`.  
To encrypt this file, we pass the encryption password we created above to ansible-vault as below.
```sh
ansible-vault encrypt roles/whatsapp/vars/variables.yml --vault-password-file ~/.vault_pass.txt
```
### Decrypting the secret variables ###
Once encrypted the file cannot be read. If you want to edit the file you can decrypt it as follows
```sh 
ansible-vault decrypt roles/whatsapp/vars/variables.yml --vault-password-file ~/.vault_pass.txt
```
### Setting up a new host ###
This software configures **Ubuntu** servers to run Ongair whatsapp agents.
To setup a new server, you will need to supply the following:
- ssh login credentials
- Hostname/IP address, 
- Accounts running on the server
- The names of upstart services for each account running on the server

Each host's credentials are added inside the `production` file which carries inventory for all production servers.  
Each host is assumed to have 1 or more whatsapp accounts and they are registered in a file named after the hostname inside the `group_vars` directory.

For example let's assume we want to add a new host whose IP address is `56.4.5.232` , hostname `ongair-56.4.5.23` with username `deploy` and 3 whatsapp accounts `93939393`, `83838833` and `6272644`

The first thing we do is add the host to the inventory as follow
```sh
[ongair-56.4.5.232]
56.4.5.232 ansible_ssh_user=deploy
```
You should be able to ssh to the server without requiring a password by simply typing `ssh deploy@56.4.5.232`.   
Then we add the host to the whatsapp group (in the same inventory file) as a child
```sh
[whatsapp:children]
....
ongair-56.4.5.232
```
### Testing the new host ###
Test if you can connect to the now host

```sh
    ansible all -i prodution -m ping --limit ongair-56.4.5.232
```
If the above fails, check your login credentials and make sure you have entered the host details correctly in the inventory.

#### Configure host agents ###
We now need to add the host's account variables inside the `group_vars` folder.
In this case we create a file named after the hostname inside group_vars `touch group_vars/ongair-56.4.5.232`.  
Inside that file we add the hosts variables (based on the account numbers above) as follows
```sh
agents:   
    - { account_number: 93939393, agent_name: ongair-93939393 }
    - { account_number: 83838833, agent_name: ongair-83838833 }
    - { account_number: 6272644, agent_name: ongair-6272644 }
```
With the above setup, the new host is now part of the ongair-whatsapp inventory and we can configure it, deploy the whatsapp code to it and restart services using this ansible software.    

New hosts need to be configured to run the whatsapp code. So the initial command on a new host should be to setup the server before attempting to deploy the code.
To configure the above host to run the whatsapp code, you can type the following 
```sh
ansible-playbook -i production setup.yml --limit ongair-56.4.5.232 --vault-password-file ~/.vault_pass.txt
```
To deploy the latest whatsapp code and restart all services in the new host,
```sh
ansible-playbook -i production deploy.yml --limit ongair-56.4.5.232 --vault-password-file ~/.vault_pass.txt
```
To run both setup and deployment procedures on the new host,
```sh
ansible-playbook -i production site.yml --limit ongair-56.4.5.232 --vault-password-file ~/.vault_pass.txt
```
#### Deploying new whatsapp code to all available servers ####

```sh
 ansible-playbook -i production deploy.yml --vault-password-file ~/.vault_pass.txt
```


# The Ongair Ansible API
The Ongair ansible allows you to programmatically carry out the above tasks but via a http API.
The API at the moment has four endpoints:
- `/trial?number=<number>` Allows you to automatically add a new number to the trial server
- `/production?number=<number>` Allows to automatically spin up a new instance based on the Ongair Whatsapp image and add a new number to it.
- `/list` - Lists all available Ongair Production Servers
- `/reload?instanceid=<instanceid>` - Allows you to reload an instance
- `/terminate?insanceid=<instanceid>` Allows you to terminate a production instance



#### Adding a number to the trial server
To add a number to the trial server, just call the trial endpoint with the number as a paramater. For example to add `0123456789` to trial we just make a GET request to the trial endpoint as follows `http://ansibleapi.ongair.im/trial?number=0123456789`

This adds the number to the trial server and returns with a response in this format
```
{
    status: 200,
    agent_name: "ongair-0123456789",
    number: "0123456789",
    message: "successfully added 0123456789 to trial",
    data: {
        52.18.43.161: {
        unreachable: 0,
        skipped: 0,
        ok: 4,
        changed: 2,
        failures: 0
        }
    },
    time_taken: "18.14 seconds"
}
```

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

## Testing ##
Test if you can connect to the servers

```
    ansible all -m ping -i hosts -u deploy
```


#!/bin/bash   
#List all the available upstart services for ongair and restart them.

# first we find the services
SERVICES=`ls /etc/init/ | grep -Po console\.*.conf`


for service in $SERVICES; do
            echo $service 
            echo `sudo service $service status`
            # re='([w]+)\.'
            re='.\.conf'
            # re='console.'
            if [[ $service =~ $re ]]; then
            	echo ${BASH_REMATCH[2]}
            fi
        done
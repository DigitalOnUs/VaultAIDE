#!/bin/bash
while true; do
	sleep 1;
	ls -d /app/ui/settings/config.db /app/ui/certificates/*.pem | entr -dp restart_nginx.sh 
done

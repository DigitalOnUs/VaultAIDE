#!/bin/bash

supervisorctl stop uwsgi
supervisorctl stop nginx
# uwsgi does not bounce the workers 
ps -A -o pid,cmd|grep  /usr/local/bin/uwsgi | grep -v grep |head  | awk '{print $1}' | xargs kill -9
sleep 1
supervisorctl start nginx
supervisorctl start uwsgi

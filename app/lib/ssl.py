from io import open
from logging import debug

def update_ssl(ssl=True , path="nginx.conf" ):
    nginxConf = open(path, 'r')
    lines = nginxConf.readlines()
    nginxConf.close()

    if ssl:
        debug("ssl is true")
        nginxConf = open(path, 'w')
        lines[17] = str.replace(lines[17], "listen 5000;", "listen 5000 ssl;")
        lines[18] = str.replace(lines[18], "listen [::]:5000;", "listen [::]:5000 ssl;")
        nginxConf.writelines(lines)
        nginxConf.close()
        return

    debug("ssl is false")
    nginxConf = open(path, 'w')
    lines[17] = str.replace(lines[17], "listen 5000 ssl;", "listen 5000;")
    lines[18] = str.replace(lines[18], "listen [::]:5000 ssl;", "listen [::]:5000;")
    nginxConf.writelines(lines)
    nginxConf.close()


FROM tiangolo/uwsgi-nginx-flask:python3.7

RUN pip install --upgrade pip

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY ./app /app

WORKDIR /app

RUN pip install -r requirements.txt
RUN mv /app/nginx/* /etc/nginx/conf.d/


RUN mkdir -p /app/ui/certificates/
RUN mkdir -p /app/ui/settings/

RUN mv /app/certs/server.cert.pem  /app/ui/certificates/nginx-selfsigned.crt.pem
RUN mv /app/certs/server.key.pem /app/ui/certificates/nginx-selfsigned.key.pem
RUN touch /app/ui/settings/config.db

VOLUME /app/ui

#Install and setup Entr script (bootstrapping)
WORKDIR ~/
RUN apt update -y && apt install entr -y
COPY ./bootstrap/entr_script.sh /usr/local/bin/entr_script.sh
RUN chmod +x /usr/local/bin/entr_script.sh
COPY ./bootstrap/restart_nginx.sh /usr/local/bin/restart_nginx.sh
RUN chmod +x /usr/local/bin/restart_nginx.sh
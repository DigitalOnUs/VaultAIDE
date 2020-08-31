import json
import logging
import time
import socket
import arrow

import logging

from tinydb import Query
from tinydb.operations import increment
from datetime import datetime

q = Query()

class AuditServer(object):
    def __init__(self, host, port, suggestions, vault, db_week, db_month):
        self.host = host
        self.port = port
        self.suggestions = suggestions
        self.vault = vault

        self.db_week = db_week
        self.db_month = db_month

    def analize(self, data):
        
        for d in data.split(b'\n'):
            if not d:
                return
            j = json.loads(d)

            print("Log info ****************", j, flush=True)

            time = j['time'].split("T")[0]
            datetime_object = datetime.strptime(time, '%Y-%m-%d')
            
            self.process_by_week(datetime_object)
            self.process_by_month(datetime_object)

            self.process_vault_log(j)

    def process_vault_log(self, data):
        if data['type'] == "request":
            return

        try:
            response = data["response"]
            request = data['request']
            auth = data['auth']

        except KeyError:
            return
        policies_array = auth.get('token_policies', [])
        
        if response.get('secret', False):
            id = response["secret"].get("lease_id", False)

            if id:
                optimizable, time, remain_time, used_time, expire_time = self.used_time_greater_than_issued(id)
                if optimizable:
                    self.suggestions.leases_ttl(expire_time, used_time, time)
            return

        elif "root" in policies_array:
            if request['path'] == "auth/token/create":
                policies_array = auth.get('token_policies', [])
                self.suggestions.high_privilege_login()
                return

            else:
                self.suggestions.high_privilege_action()
                return
    
    def process_by_week(self, log_date):
        log_week = log_date.isocalendar()[1]
        log_year = log_date.year

        found = self.db_week.search((q.year == log_year) & (q.week == log_week))

        if not found:
            self.db_week.insert({'week': log_week, 'year': log_year, 'total': 1})
        else:
            self.db_week.update(increment('total'), ((q.year == log_year) & (q.week == log_week)))

        self.db_week.close()

    def process_by_month(self, log_date):
        log_month = log_date.month
        log_year = log_date.year

        found = self.db_month.search((q.year == log_year) & (q.month == log_month))

        if not found:
            self.db_month.insert({'month': log_month, 'year': log_year, 'total': 1})
        else:
            self.db_month.update(increment('total'), ((q.year == log_year) & (q.month == log_month)))

        self.db_month.close()

    def used_time_greater_than_issued(self, id):
        response = self.vault.client.sys.read_lease(
            lease_id = id,
        )

        expire_time = arrow.get(response["data"]["expire_time"])
        issue_time = arrow.get(response["data"]["issue_time"])
        now = arrow.utcnow().to("local")

        remain_time = expire_time - now
        used_time = now - issue_time

        return remain_time > used_time, remain_time - used_time, remain_time, used_time, expire_time
    
    def serve(self):
        logging.info("***** Starting socket for AUDIT ********* ")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # python to re-use socket left in TIME_WAIT by a kill process
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            conn, addr = s.accept()
            with conn:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break

                    self.analize(data)
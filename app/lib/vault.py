from lib.github import Github
from datetime import datetime

import hvac
import requests
import json

class VaultClient:
    def __init__(self, addr, token, pickledb_obj, db_week, db_month, verify=False):
        self.github = Github()
        self.token = token
        self.addr = addr
        self.client = hvac.Client(addr, token)

        self.db = pickledb_obj
        self.db_week = db_week
        self.db_month = db_month

        # verify by default is false
        self.verify = verify


    '''
        General functions
    '''
    def cleanup_json(self, data):
        cleaned = dict()
        for k,v in data.items():
            if v is None or v == '':
                continue

            cleaned[k] = v
        return cleaned

    def query_vault(self, path):
        url = self.addr + path
        return self.cleanup_json(requests.get(
            url,
            headers={'X-Vault-Token': self.token, 'X-Vault-Namespace': "root/"},
            verify=self.verify
        ).json())


    '''
        HVAC General Functions
    '''
    def is_authenticated(self):
        return self.client.is_authenticated()

    def get_status(self):
        if not self.is_authenticated():
            return None

        return self.client.sys.read_health_status(method='GET')

    def is_root(self):
        data = self.get_identity()
        path = data.get('path')
        policies = data.get('policies')
        return path == 'auth/token/root' or 'root' in policies

    def get_identity(self):
        return self.client.lookup_token().get('data')

    def get_audit_devices(self):
        return self.client.sys.list_enabled_audit_devices().get('data')

    def is_initialized(self):
        return self.client.is_initialized()

    def get_policies(self):
        return self.client.sys.list_policies().get('data').get('policies')

    def get_metricts(self):
        return self.query_vault("/v1/sys/metrics?format=")

    def get_expire_leases(self):
        return self.query_vault("/v1/sys/leases")

    def audit_device_status(self):
        return self.query_vault("/v1/sys/audit")

    def get_configuration(self):
        return self.query_vault("/v1/sys/config/state/sanitized")

    def get_health(self):
        return self.query_vault("/v1/sys/health")

    def get_general_information(self):
        return self.query_vault("/v1/sys/host-info")

    def get_version(self):
        return self.query_vault("/v1/sys/health")['version']

    def get_features(self):
        return self.query_vault("/v1/sys/license")

    def get_integrated_apps(self):
        return self.query_vault("/v1/sys/mounts")

    def wrapping(self, function):
        return self.query_vault("/v1/sys/wrapping/" + function)

    def get_roles(self):
        return self.query_vault("/v1/auth/token/roles")

    def get_secrets_engine_list(self):
        return self.client.sys.list_mounted_secrets_engines()['data'].keys()

    def get_auth_methods(self):
        return self.client.sys.list_auth_methods()['data']

    '''
        Adoption Statistics
    '''
        # Adoption Stat 1 Functions
    def get_overall_week(self):

        curr_week = datetime.today().isocalendar()[1]
        curr_year = datetime.today().year

        found = self.db_week.search((q.year == curr_year) & (q.week == curr_week))

        if not found:
            return "Negative :arrow_down:"

        found_last = self.db_week.search((q.year == curr_year) & (q.week == (curr_week - 1)))

        if not found_last:
            return "Positive :arrow_up:"

        if found[0]['total'] > found_last[0]['total']:
            return "Positive :arrow_up:"
        else:
            return "Negative :arrow_down:"

    def get_overall_month(self):
        curr_month = datetime.today().month
        curr_year = datetime.today().year

        found = self.db_month.search((q.year == curr_year) & (q.month == curr_month))

        if not found:
            return "Negative :arrow_down:"

        found_last = self.db_month.search((q.year == curr_year) & (q.month == (curr_month - 1)))

        if not found_last:
            return "Positive :arrow_up:"

        if found[0]['total'] > found_last[0]['total']:
            return "Positive :arrow_up:"
        else:
            return "Negative :arrow_down:"

    def vault_operations(self):
        curr_month = datetime.today().month
        curr_year = datetime.today().year

        found = self.db_month.search((q.year == curr_year) & (q.month == curr_month))

        if not found:
            return 0
        else:
            return found[0]['total']

    # Adoption Stat 2 Functions
    def get_total_entities_count(self):
        return requests.request('LIST',
                self.addr + "/v1/identity/entity/id",
                headers={'X-Vault-Token': self.token, 'X-Vault-Namespace': "root/"},
                verify=self.verify
            ).json().get('data', {})

    def get_total_roles(self):
        total_roles = 0

        mount_keys = requests.get(self.addr + "/v1/sys/auth",
                headers={'X-Vault-Token': self.token, 'X-Vault-Namespace': "root/"},
                verify=self.verify
            ).json()['data'].keys()

        mounts = [k for k in mount_keys]

        for mount in mounts:
            plain_users = requests.request('LIST',
                self.addr + "/sys/auth" + mount + "/users",
                headers={'X-Vault-Token': self.token, 'X-Vault-Namespace': "root/"},
                verify=self.verify
            ).json().get('data', {}).get('keys', [])

            users = len(plain_users)

            print("*************", users, flush=True)

            plain_roles = requests.request('LIST',
                self.addr + "/sys/auth" + mount + "/roles",
                headers={'X-Vault-Token': self.token, 'X-Vault-Namespace': "root/"},
                verify=self.verify
            ).json().get('data', {}).get('keys', [])

            roles = len(plain_roles)

            print("+++++++++++++", roles, flush=True)

            total_roles = total_roles + users + roles

        return total_roles

    def get_total_tokens(self):
        total_tokens = 0

        accesor_keys = requests.request('LIST',
                self.addr + "/v1/auth/token/accessors",
                headers={'X-Vault-Token': self.token, 'X-Vault-Namespace': "root/"},
                verify=self.verify
            ).json().get('data', {}).get('keys', [])

        total_tokens = len(accesor_keys)

        return total_tokens

    def get_change_percentage(self):

        curr_month = datetime.today().month
        curr_year = datetime.today().year

        found = self.db_month.search((q.year == curr_year) & (q.month == curr_month))
        total_year = self.db_month.search(q.year == curr_year)

        if not found:
            return "0%"

        total_operations = 0

        for month in total_year:
            total_operations = total_operations + month['total']

        change_percentage = divmod((found['total'] * 100), total_operations)[0]

        return str(change_percentage) + "%"
        

    '''
        Extant Leases Functions
    '''
    def get_total_leases(self):

        token_accessors = requests.request('LIST',
                self.addr + "/v1/sys/leases/lookup/auth/token/create",
                headers={'X-Vault-Token': self.token},
                verify=self.verify
            ).json()

        accesor_array = token_accessors.get('data', {}).get('keys', [])

        total_leases = len(accesor_array)

        return total_leases

    def get_leases_detail(self):
        longest_ttl = None
        shortest_ttl = None
        longest = None
        shortest = None
        renewable = 0
        non_renewable = 0
        infinite_ttl = 0

        token_accessors = requests.request('LIST',
                self.addr + "/v1/sys/leases/lookup/auth/token/create",
                headers={'X-Vault-Token': self.token},
                verify=self.verify
            ).json()

        accesor_array = token_accessors.get('data', {}).get('keys', [])

        for accesor in accesor_array:

            lease_id = "auth/token/create/" + accesor
            put_data = "{\"lease_id\": \"auth/token/create/" + accesor + "\"}"

            lease_info = requests.request('PUT',
                self.addr + "/v1/sys/leases/lookup",
                headers={'X-Vault-Token': self.token},
                data=put_data,
                verify=self.verify
            ).json()

            expire_time = lease_info.get('data', {}).get('expire_time', False)
            is_renewable = lease_info.get('data', {}).get('renewable', False)
            lease_ttl = lease_info.get('data', {}).get('ttl', False)

            if longest_ttl == None:
                longest_ttl = lease_ttl
                longest = expire_time
            else:
                if longest_ttl < lease_ttl:
                    longest_ttl = lease_ttl
                    longest = expire_time


            if shortest_ttl == None:
                if lease_ttl > 0:
                    shortest_ttl = lease_ttl
                    shortest = expire_time
            else:
                if shortest_ttl > lease_ttl and lease_ttl > 0:
                    shortest_ttl = lease_ttl
                    shortest = expire_time

            if is_renewable:
                renewable += 1
            else:
                non_renewable += 1

            if lease_ttl == 0:
                infinite_ttl += 1

        # Formating dates 2020-03-09T20:13:17.838583701Z
        if shortest is not None:
            short = shortest.split("T")
            time = short[1].split(".")[0]
            date_time_short = short[0] + " " + time
        else:
            date_time_short = ""

        if longest is not None:
            long_t = longest.split("T")
            time = long_t[1].split(".")[0]
            date_time_long = long_t[0] + " " + time
        else:
            date_time_long = ""

        detail_data = { "longest": date_time_long,
                        "shortest": date_time_short,
                        "shortest_ttl": shortest_ttl,
                        "longest_ttl": longest_ttl,
                        "renewable": renewable,
                        "non_renewable": non_renewable,
                        "infinite_ttl": infinite_ttl
                      }

        return detail_data

        '''
            Lease data
            {'request_id': '30439b26-762a-629e-4b1f-35c35c2ea1e7', 'lease_id': '',
            'renewable': False, 'lease_duration': 0,
            'data': {'expire_time': None, 'id': 'auth/token/create/e3bf69abeea8f32f00111f17128fa5e5a25d6b07',
            'issue_time': '2020-03-09T18:53:14.609577415Z',
            'last_renewal': None, 'renewable': False, 'ttl': 0},
            'wrap_info': None, 'warnings': None, 'auth': None}
        '''

    '''
        Score check
    '''
    def vault_posture_score(self, thread=False):
        score = 0
        accesor_ttl = []

        if thread:
            self.slack_client.api_call("chat.postMessage", channel=channel, text="Details", thread_ts = thread)

        versions = self.github.get_latest_releases()
        current = self.get_version()
        latest = versions[0].lstrip('v')

        if latest == current:
            score += 20
            if thread:
                self.slack_client.api_call("chat.postMessage", channel=channel, text="Latest version of Vault: :white_check_mark:", thread_ts = thread)
        else:
            if thread:
                self.slack_client.api_call("chat.postMessage", channel=channel, text="Latest version of Vault: :x:", thread_ts = thread)

        if self.db.get_data('vault_tls'):
            score += 20
            if thread:
                self.slack_client.api_call("chat.postMessage", channel=channel, text="TLS enabled: :white_check_mark:", thread_ts = thread)
        else:
            if thread:
                self.slack_client.api_call("chat.postMessage", channel=channel, text="TLS enabled: :x:", thread_ts = thread)

        auth_methods = [k  for  k in self.get_auth_methods()]

        if len(auth_methods) > 1:
            score += 20
            if thread:
                self.slack_client.api_call("chat.postMessage", channel=channel, text="Using secure auth methods: :white_check_mark:", thread_ts = thread)
        else:
            self.slack_client.api_call("chat.postMessage", channel=channel, text="Using secure auth methods: :x:", thread_ts = thread)

        token_accessors = requests.request('LIST',
                self.addr + "/v1/sys/leases/lookup/auth/token/create",
                headers={'X-Vault-Token': self.token},
                verify=self.verify
            ).json()

        accesor_array = token_accessors.get('data', {}).get('keys', [])

        for accesor in accesor_array:
            info = requests.request('PUT',
                self.addr + "/v1/sys/leases/lookup",
                headers={'X-Vault-Token': self.token},
                data="{\"lease_id\": \"auth/token/create/" + accesor + "\"}",
                verify=self.verify
            ).json()

            accesor_ttl.append(info['data']['ttl'])


        if 0 in accesor_ttl:
            self.slack_client.api_call("chat.postMessage", channel=channel, text="No periodic admin tokens: :x:", thread_ts = thread)
        else:
            score += 20
            self.slack_client.api_call("chat.postMessage", channel=channel, text="No periodic admin tokens: :white_check_mark:", thread_ts = thread)


        score += 20
        self.slack_client.api_call("chat.postMessage", channel=channel, text="Disabled root token: :white_check_mark:", thread_ts = thread)

        return str(score) + "/100"


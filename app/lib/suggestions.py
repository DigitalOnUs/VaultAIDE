from slackclient import SlackClient
from lib.github import Github

class Suggestions:
    def __init__(self, vault_client, pickledb_obj={}):
        self.vault_client = vault_client

        self.db = pickledb_obj

        self.sl_token = self.db.get_data('slack_token')
        self.slack_client = SlackClient(self.sl_token)
        self.channel = self.db.get_data('slack_channel')

    def suggest_version(self):
    	'''
    		Version updates
    	'''
        versions = self.github.get_latest_releases()
        current = self.vault.get_version()
        latest = versions[0].lstrip('v')

        if not latest == current:
            # Suggestion
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Suggestion: Update Vault.")

            # Reason
            because = "Because: You currently have a {}, and there is an update, Version {}.".format(current, latest)
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text=because)

            # Action
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Action: Download")

            # Source
            text = "https://releases.hashicorp.com/vault/" + latest + "/vault_" + latest + "_linux_amd64.zip"
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text=text)

            text2 = "and install it to vaultserver1.uat.acmecorp.net, vaultserver2.uat.acmecorp.net, and vaultserver3.uat.acmecorp.net."
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text=text2)

            text3 = "Hashi Docs: https://www.vaultproject.io/docs/upgrading/index.html#ha-installations"
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text=text3)

            # Internal docs
            internal = "Internal docs for this: confluence.acmecorp.net/vault-upgrade-manualconfluence.acmecorp.net/vault-upgrade-ansible"
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text=internal)
        
        else:
            latest_version = 'You already have the latest version of Vault installed: {}'.format(current)
            self.slack_client.api_call("chat.postMessage", channel=self.channel, text=latest_version)


        return True

    def adoption_stats(self):
    	'''
    		Adoption Statistics
    	'''
        secrets_engine = len([k  for  k in self.vault.get_secrets_engine_list()])
        auth_methods = len([k  for  k in self.vault.get_auth_methods()])
        policies = len([k  for  k in self.vault.get_policies()])
        total_operations = self.vault.vault_operations()

        # Suggestion
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*Adoption Stats.* :bar_chart:")

        # Check Logs
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Overall Adoption rate this week: {}".format(self.vault.get_overall_week()))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Overall Adoption rate this month: {}".format(self.vault.get_overall_month()))

        # Dummy data
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Vault Operations this month: {}".format(total_operations))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Monthly BVA: ${} (Estimated)".format(total_operations * 500))

        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} Auth Methods".format(auth_methods))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} Policies".format(policies))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} Secrets Engines".format(secrets_engine))

        # More Details
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="_Respond 'Adoption Details 2' for more._")

        return True

    def adoption_stats_detailed(self):
    	'''
    		Adoption Statistics Detailed
    	'''

        total_entities = self.vault.get_total_entities_count().get('keys', [])

        # Suggestion
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*Adoption Details* :bar_chart:")

        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Total Entities: {}".format(len(total_entities)))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Total Roles: {}".format(self.vault.get_total_roles()))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Total Tokens: {}".format(self.vault.get_total_tokens()))

        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Change: {}".format(self.vault.get_change_percentage()))

        return False

    def extant_leases(self):
    	'''
    		Leases information
    	'''
        leases_detail = self.vault.get_leases_detail()
        
        # Suggestion
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*Extant Leases*")

        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="You have {} leases in Vault".format(self.vault.get_total_leases()))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} non renewable".format(leases_detail['non_renewable']))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} renewable".format(leases_detail['renewable']))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Longest expire time: {}".format(leases_detail['longest']))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Longest remaining ttl: {}".format(leases_detail['longest_ttl']))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Shortest expire time: {}".format(leases_detail['shortest'], leases_detail['shortest']))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Shortest remaining ttl: {}".format(leases_detail['shortest_ttl']))
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Never expire: {}".format(leases_detail['infinite_ttl']))

    	return True

    def total_tokens(self):
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*Tokens*")
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} total".format(self.vault.get_total_tokens()))

        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} service tokens".format())
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} batch tokens".format())
        # self.slack_client.api_call("chat.postMessage", channel=self.channel, text="{} periodic Tokens".format(self.vault.get_auth_methods(namespace = namespace)))

        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*Oldest:* {}".format())
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*Newest:* {}".format())

        return True

    def high_privilege_login(self):
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*:warning: WARNING: ROOT ACCOUNT CREATED IN PRODUCTION*")     
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="If you're not aware of this as part of an authorized break-glass operation, Seal the Vault:") 
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="vault login && vault operator seal")
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="For more information about this visit https://www.vaultproject.io/docs/commands/operator/seal/")
 		
 		return True

    def high_privilege_action(self):
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*:warning: WARNING: ROOT ACCOUNT USED IN PRODUCTION*")     
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="If you're not aware of this as part of an authorized break-glass operation, Seal the Vault:") 
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="vault login && vault operator seal")
        self.slack_client.api_call("chat.postMessage", channel=self.channel, text="For more information about this visit https://www.vaultproject.io/docs/commands/operator/seal/")

        return True

    def vault_posture_score(self):
        score = self.vault.vault_posture_score()

        self.slack_client.api_call("chat.postMessage", channel=channel, text="*VaultPosture Score: {}*".format(score))
        self.slack_client.api_call("chat.postMessage", channel=channel, text="_Respond 'Adoption Score Details' for more._")

        return True

    def score_details(self, thread=False):
        score = self.vault.vault_posture_score(thread = thread)

        return True

    def auth_method_suggestion(self):
        auth_methods = [k  for  k in self.vault.get_auth_methods()]
        
        if len(auth_methods) > 1:
            for auth in auth_methods:
                if auth == "aws/":
                    self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Auth Method Suggestion Available")
                    self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Detected AWS platform. Use AWS Auto-Unseal?")
                    self.slack_client.api_call("chat.postMessage", channel=self.channel, text="To know more about secure auth methods visit:")
                    self.slack_client.api_call("chat.postMessage", channel=self.channel, text="https://www.vaultproject.io/docs/configuration/seal/awskms")

        
        else:
            if auth_methods[0] == "userpass/":
                self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Auth Method Suggestion Available")
                self.slack_client.api_call("chat.postMessage", channel=self.channel, text="You are using UserPass as your only auth method")
                self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Add more secure auth methods like LDAP or AppRole")
                self.slack_client.api_call("chat.postMessage", channel=self.channel, text="To know more about secure auth methods visit:")
                self.slack_client.api_call("chat.postMessage", channel=self.channel, text="https://www.vaultproject.io/docs/auth")

        return True

    def statusserer(self):
    	status = self.vault.get_health()

    	if status.get('version', False):
    		seal_state = "Sealed" if status['sealed'] == False else "Unsealed"
    		init = "Not Initialized" if status['initialized'] == False else "Initialized"
    		perf_mode = status['replication_perf_mode']
    		auth_methods = len([k  for  k in self.vault.get_auth_methods()])
    		policies = len([k  for  k in self.vault.get_policies()])
    		audit_log = self.vault.audit_device_status()

    		self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Vault is reachable :white_check_mark:")
    		self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Vault seal state: ".format(seal_state))
    		self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Vault: ".format(init))
    		self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Replication Status: ".format(perf_mode))
    		
    		if auth_methods <= 1:
    			self.slack_client.api_call("chat.postMessage", channel=self.channel, text="You are using UserPass as your only auth method")

    		if policies == 0:
    			self.slack_client.api_call("chat.postMessage", channel=self.channel, text="You don't have any Vault policies present")
    		else:
    			self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Vault policies present")

    		if audit_log == {}:
    			self.slack_client.api_call("chat.postMessage", channel=self.channel, text="You don't have the audit logs enabled")
    		else:
    			self.slack_client.api_call("chat.postMessage", channel=self.channel, text="Vault Audit Logs enabled")
    	else:
    		self.slack_client.api_call("chat.postMessage", channel=self.channel, text="*:warning: WARNING: Vault is not reachable*")

    	return True

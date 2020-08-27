class Suggestions:
    def __init__(self, vault_client, pickledb_obj={}):
        self.vault_client = vault_client

        self.db = pickledb_obj

        self.sl_token = self.db.get_data('slack_token')
        self.slack_client = SlackClient(self.sl_token)
        self.channel = self.db.get_data('slack_channel')
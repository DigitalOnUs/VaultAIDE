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
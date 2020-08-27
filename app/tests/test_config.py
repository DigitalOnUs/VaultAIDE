import pickledb

''' Entry just placeholder for injecting config (no pythonic)'''
class ComponentEntry(object):
    def __init__(self, name):
        # <name>_<property_name>
        self._name = name
        # properties
        self._address = None
        self._token = None
        self._port = None
        self._tls_enable = None
        self._channel = None
        self._host = None

        # schema 
        self.schema = {
            "address" : self.set_address,
            "token" : self.set_token,
            "port" : self.set_port,
            "tls_enable" : self.set_tls_enable,
            "channel" : self.set_channel,
            "host" : self.set_host
        }

    @property
    def name(self):
        return self._name
    @property
    def address(self):
        return self._address
    @property
    def token(self):
        return self._token
    @property
    def port(self):
        return self._port
    @property
    def tls_enable(self):
        return self._tls_enable
    @property
    def channel(self):
        return self._channel
    @property
    def host(self):
        return self._host 
    
    def load_from_chache(self,loader):
        for prop in self.schema:
            property_name = "{}_{}".format(self._name, prop)
            foo = self.schema[prop]
            foo(loader.get(property_name))
        return self

    def set_address(self, address):
        self._address = address
    def set_token(self, token):
        self._token = token
    def set_port(self,port):
        self._port = port
    def set_tls_enable(self, tls_enable):
        self._tls_enable = tls_enable
    def set_channel(self, channel):
        self._channel = channel
    def set_host(self, host):
        self._host = host


class Cache(object):
    def __init__(self, cache_dir):
        self.cache_file = cache_dir
        self._vault = None
        self._audit_device = None
        self._slack = None

        self.index = {
            "vault": self.set_vault,
            "audit_device" : self.set_audit_device,
            "slack": self.set_slack,
        }

        # db
        self.db = pickledb.load(self.cache_file, False)

        for name in self.index:
            component = ComponentEntry(name).load_from_chache(self.db)
            foo = self.index[name]
            foo(component)
    
    @property
    def vault(self):
        return self._vault
    
    @property
    def audit_device(self):
        return self._audit_device
    
    @property
    def slack(self):
        return self._slack

    def set_vault(self, vault):
        self._vault = vault
    
    def set_audit_device(self, audit_device):
        self._audit_device = audit_device
    
    def set_slack(self, slack):
        self._slack = slack 

''' initialization '''
def test_init():
    cache_name = "test.db"
    db = pickledb.load(cache_name, False)
    ''' initial args '''
    vault_address = "https://vault:8200"
    vault_token = "mytoken"

    ''' populating info '''
    db.set('vault_address',  vault_address)
    db.set('vault_token', vault_token)

    arr_token = ("xoxb", "918589458594", "931400580288", "9LrOqSiT1GEKFftbqrfRXhD4")
    sl_token = "-".join(arr_token)
    sl_channel = '#vaultbot'

    db.set('slack_token', sl_token)
    db.set('slack_channel', sl_channel)

    audit_device_host = '0.0.0.0'
    audit_device_port = 9090

    db.set('audit_device_host', audit_device_host )
    db.set('audit_device_port', audit_device_port )

    db.dump()

    cache = Cache(cache_name)

    ''' just making sure the cache saves everything '''
    assert cache.vault.address == vault_address
    assert cache.vault.token == vault_token
    
    assert cache.slack.token == sl_token
    assert cache.slack.channel == sl_channel

    print(cache.audit_device)

    assert cache.audit_device.host == audit_device_host
    assert cache.audit_device.port == audit_device_port
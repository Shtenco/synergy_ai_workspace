from avito_ai_combine.avito.auth import AuthClient
from avito_ai_combine.avito.transport import AvitoTransport
from avito_ai_combine.avito.account import AccountClient
from avito_ai_combine.avito.scopes import CapabilityResolver
class ConnectionService:
    def __init__(self,account_client,capabilities): self.account_client=account_client; self.capabilities=capabilities
    def check(self):
        account=self.account_client.get_self(); account_id=str(account.get('id') or account.get('user_id') or '')
        caps=self.capabilities.resolve(account_id) if hasattr(self.capabilities,'resolve') else self.capabilities
        mapping={'messenger_read':'messenger:read','messenger_write':'messenger:write','listings_read':'listings:read','stats_read':'stats:read','autoload':'autoload','promotion':'promotion','reviews':'reviews','calls':'calls'}
        return {'ok':True,'account':account,'capabilities':{n:caps.allows(scope) for n,scope in mapping.items()}}
class ConnectionManager:
    def __init__(self,runtime,auth_client=None,transport=None):
        self.rt=runtime; self.auth=auth_client or AuthClient(); self.transport=transport or AvitoTransport(base_url=runtime.config.base_url)
    def save_credentials(self,client_id,client_secret):
        self.rt.config.client_id=client_id.strip(); self.rt.config.save(self.rt.data_dir/'config.json')
        self.rt.vault.put('client_secret',client_secret.strip()); self.rt.vault.save(); return True
    def check_live(self):
        secret=self.rt.vault.get('client_secret')
        if not self.rt.config.client_id or not secret: return {'ok':False,'reason':'not_configured'}
        token=self.auth.client_credentials(self.rt.config.client_id,secret); self.rt.token=token; self.rt.transport=self.transport
        account_client=AccountClient(self.transport,token.access_token); caps=CapabilityResolver(scopes=token.scopes)
        result=ConnectionService(account_client,caps).check(); self.rt.account_id=str(result['account'].get('id') or result['account'].get('user_id') or ''); self.rt.capabilities=caps
        import json
        with self.rt.db.transaction() as c:
            c.execute('insert or replace into avito_accounts(id,external_id,account_id,data) values ((select id from avito_accounts where external_id=?),?,?,?)',(self.rt.account_id,self.rt.account_id,self.rt.account_id,json.dumps(result['account'],ensure_ascii=False)))
            c.execute('delete from account_capabilities where account_id=?',(self.rt.account_id,)); c.execute('insert into account_capabilities(external_id,account_id,data) values (?,?,?)',('current',self.rt.account_id,json.dumps(result['capabilities'])))
        return result

from dataclasses import dataclass
from pathlib import Path
from avito_ai_combine.app.config import AvitoConfig
from avito_ai_combine.app.events import EventBus
from avito_ai_combine.security.session_key import SessionKeyManager
from avito_ai_combine.security.vault import CredentialVault
from avito_ai_combine.storage.db import Database
from avito_ai_combine.storage.migrations import MigrationRunner
from avito_ai_combine.ai.knowledge import KnowledgeService
from avito_ai_combine.avito.auth import AuthClient,TokenSet
from avito_ai_combine.avito.transport import AvitoTransport
from avito_ai_combine.avito.account import AccountClient
from avito_ai_combine.avito.scopes import CapabilityResolver
from avito_ai_combine.webhooks.handlers import WebhookHandler

@dataclass
class LocalRuntime:
    data_dir:Path; config:AvitoConfig; vault:CredentialVault; db:Database; events:EventBus; knowledge:KnowledgeService
    token:TokenSet|None=None; transport:object|None=None; account_id:str=''; capabilities:object|None=None; webhook_handler:object|None=None; account_client:object|None=None

def build_local_runtime(data_dir):
    data_dir=Path(data_dir); data_dir.mkdir(parents=True,exist_ok=True)
    cfg=AvitoConfig.load(data_dir/'config.json')
    key=SessionKeyManager(data_dir/'.vault.key').start()
    vault=CredentialVault(key,data_dir/'credentials.enc').load()
    db=Database(data_dir/'avito_ai_combine.sqlite3'); MigrationRunner.apply(db)
    events=EventBus(); rt=LocalRuntime(data_dir,cfg,vault,db,events,KnowledgeService())
    rt.webhook_handler=WebhookHandler(db,events,lambda:rt.account_id)
    return rt

LiveRuntime=LocalRuntime

def build_live_runtime(data_dir,*,client_id='',client_secret='',acquire_token=False,auth_client=None,transport=None):
    rt=build_local_runtime(data_dir)
    if client_id: rt.config.client_id=client_id
    rt.config.save(rt.data_dir/'config.json')
    if client_secret: rt.vault.put('client_secret',client_secret); rt.vault.save()
    rt.transport=transport or AvitoTransport(base_url=rt.config.base_url)
    if acquire_token:
        secret=client_secret or rt.vault.get('client_secret')
        if not rt.config.client_id or not secret: raise ValueError('client_id and client_secret are required')
        auth=auth_client or AuthClient(); rt.token=auth.client_credentials(rt.config.client_id,secret)
        rt.account_client=AccountClient(rt.transport,rt.token.access_token)
        rt.capabilities=CapabilityResolver(scopes=rt.token.scopes)
    return rt

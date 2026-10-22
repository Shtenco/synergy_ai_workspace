from pathlib import Path
from avito_ai_combine.app.config import AvitoConfig
from avito_ai_combine.security.vault import CredentialVault
from avito_ai_combine.security.session_key import SessionKeyManager

def test_config_round_trip_contains_no_secret(tmp_path):
    cfg=AvitoConfig(client_id='cid', auth_mode='client_credentials', webhook_url='https://example.test/hook')
    p=tmp_path/'config.json'; cfg.save(p); raw=p.read_text()
    assert 'client_secret' not in raw and 'access_token' not in raw
    loaded=AvitoConfig.load(p)
    assert loaded.client_id=='cid' and loaded.webhook_url.endswith('/hook')

def test_vault_can_persist_ciphertext_file(tmp_path):
    key=SessionKeyManager().start()
    p=tmp_path/'credentials.enc'
    v=CredentialVault(key,p); v.put('client_secret','S'); v.save()
    assert '"S"' not in p.read_text()
    v2=CredentialVault(key,p); v2.load(); assert v2.get('client_secret')=='S'

from avito_ai_combine.app.bootstrap import build_live_runtime

def test_live_runtime_builds_from_config_without_network(tmp_path):
    rt=build_live_runtime(tmp_path, client_id='cid', client_secret='sec', acquire_token=False)
    assert rt.config.client_id=='cid'
    assert rt.vault.get('client_secret')=='sec'
    assert rt.transport.base_url=='https://api.avito.ru'
    assert rt.account_client is None

def test_live_runtime_can_acquire_token_and_wire_account(tmp_path):
    class FakeAuth:
        def client_credentials(self,cid,secret):
            from avito_ai_combine.avito.auth import TokenSet
            return TokenSet('AT',expires_in=3600,scopes=frozenset({'messenger:read'}))
    rt=build_live_runtime(tmp_path, client_id='cid', client_secret='sec', acquire_token=True, auth_client=FakeAuth())
    assert rt.token.access_token=='AT'
    assert rt.account_client is not None

"""Real localhost HTTP assertions, no external provider traffic."""
import json
import threading
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from workspace import service


def test_http_local_lead_to_approval_to_denied_external(tmp_path, monkeypatch):
    monkeypatch.setattr(service, 'DB', tmp_path / 'e2e.sqlite3')
    monkeypatch.setattr(service, 'TOKEN', 'test-in-memory-token')
    server = ThreadingHTTPServer(('127.0.0.1', 0), service.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = 'http://127.0.0.1:%d' % server.server_port

    def call(path, method='GET', obj=None):
        data = json.dumps(obj).encode() if obj is not None else None
        req = urllib.request.Request(base + path, data=data, method=method,
            headers={'Authorization':'Bearer test-in-memory-token', 'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    try:
        status, lead = call('/v1/leads','POST', {'name':'Test contact','source':'avito'})
        assert status == 201
        status, draft = call('/v1/actions/prepare','POST', {'lead_id':lead['id'], 'kind':'avito.message','draft':'Draft only, no sending'})
        assert status == 201
        aid = draft['id']
        status, approved = call(f'/v1/actions/{aid}/approve','POST', {})
        assert status == 200 and approved['status']=='approved'
        status, blocked = call(f'/v1/actions/{aid}/execute','POST', {})
        assert status == 409 and blocked['external_effects'] is False
        status, audit = call('/v1/audit')
        assert status == 200 and any(x['action']=='action.execute_denied' for x in audit['items'])
        status, providers = call('/v1/providers')
        assert status == 200
        req=urllib.request.Request(base+'/v1/leads')
        try:
            urllib.request.urlopen(req,timeout=4)
            assert False,'Unauthorized request unexpectedly succeeded'
        except urllib.error.HTTPError as exc:
            assert exc.code == 401
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_sqlite_context_always_closes(tmp_path, monkeypatch):
    monkeypatch.setattr(service, 'DB', tmp_path / 'close.sqlite3')
    db = service.connect()
    with db:
        db.execute('SELECT 1').fetchone()
    import sqlite3
    try:
        db.execute('SELECT 1')
        assert False,'connection remained open'
    except sqlite3.ProgrammingError:
        pass

import json
from avito_ai_combine.main import main

def test_cli_check_live_reports_not_configured_without_secrets(tmp_path,capsys):
    rc=main(['--check-live','--data-dir',str(tmp_path)])
    out=json.loads(capsys.readouterr().out)
    assert rc==2
    assert out['ok'] is False and out['reason']=='not_configured'

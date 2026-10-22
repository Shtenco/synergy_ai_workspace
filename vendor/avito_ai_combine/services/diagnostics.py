import json
from avito_ai_combine.security.redaction import redact_mapping
class DiagnosticsService:
    def __init__(self,state): self.state=state
    def snapshot(self): return redact_mapping(self.state)
    def export_redacted_bundle(self,path):
        path.write_text(json.dumps(self.snapshot(),ensure_ascii=False,indent=2),encoding='utf-8'); return path

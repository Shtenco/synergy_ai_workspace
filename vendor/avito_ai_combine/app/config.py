from dataclasses import dataclass,asdict
from pathlib import Path
import json
@dataclass
class AvitoConfig:
    client_id:str=''
    auth_mode:str='client_credentials'
    webhook_url:str=''
    base_url:str='https://api.avito.ru'
    autonomy_mode:str='COPILOT'
    def save(self,path):
        p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(asdict(self),ensure_ascii=False,indent=2),encoding='utf-8')
    @classmethod
    def load(cls,path):
        p=Path(path)
        return cls(**json.loads(p.read_text(encoding='utf-8'))) if p.exists() else cls()

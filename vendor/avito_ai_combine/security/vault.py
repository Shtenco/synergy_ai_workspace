from cryptography.fernet import Fernet
from pathlib import Path
import base64, hashlib, json
class CredentialVault:
    def __init__(self,key:bytes,path=None): self._f=Fernet(base64.urlsafe_b64encode(hashlib.sha256(key).digest())); self._store={}; self.path=Path(path) if path else None
    def put(self,name,value): self._store[name]=self._f.encrypt(value.encode()).decode()
    def get(self,name,default=None):
        if name not in self._store:return default
        return self._f.decrypt(self._store[name].encode()).decode()
    def delete(self,name): self._store.pop(name,None)
    def ciphertext(self,name): return self._store[name]
    def save(self,path=None):
        p=Path(path) if path else self.path
        if not p: raise ValueError('vault path is required')
        p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(self._store),encoding='utf-8')
    def load(self,path=None):
        p=Path(path) if path else self.path
        if p and p.exists(): self._store=json.loads(p.read_text(encoding='utf-8'))
        return self

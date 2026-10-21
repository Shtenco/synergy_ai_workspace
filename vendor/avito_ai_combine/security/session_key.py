import os
from pathlib import Path
class SessionKeyManager:
    def __init__(self,key_path=None): self._key=None; self.key_path=Path(key_path) if key_path else None
    def start(self):
        if self._key is not None: return self._key
        if self.key_path and self.key_path.exists(): self._key=self.key_path.read_bytes()
        else:
            self._key=os.urandom(32)
            if self.key_path:
                self.key_path.parent.mkdir(parents=True,exist_ok=True); self.key_path.write_bytes(self._key)
                try: os.chmod(self.key_path,0o600)
                except OSError: pass
        return self._key
    def reset(self): self._key=None

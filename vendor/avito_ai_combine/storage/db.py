import sqlite3
from pathlib import Path
from contextlib import contextmanager
from avito_ai_combine.app.exceptions import DatabaseIntegrityError
class Database:
    def __init__(self,path:Path): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
    def connect(self):
        try:
            c=sqlite3.connect(self.path, timeout=10); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON'); return c
        except sqlite3.DatabaseError as e: raise DatabaseIntegrityError(str(e)) from e
    @contextmanager
    def transaction(self):
        c=self.connect()
        try: yield c; c.commit()
        except Exception: c.rollback(); raise
        finally: c.close()
    def integrity_check(self):
        try:
            with self.connect() as c: ok=c.execute('PRAGMA integrity_check').fetchone()[0]
        except sqlite3.DatabaseError as e: raise DatabaseIntegrityError(str(e)) from e
        if ok!='ok': raise DatabaseIntegrityError(ok)
        return True
    def table_names(self):
        with self.connect() as c: return {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
    def execute(self,sql,params=()):
        with self.transaction() as c: return c.execute(sql,params).rowcount
    def query(self,sql,params=()):
        with self.connect() as c: return [dict(r) for r in c.execute(sql,params).fetchall()]
    def scalar(self,sql,params=()):
        with self.connect() as c:
            r=c.execute(sql,params).fetchone(); return r[0] if r else None

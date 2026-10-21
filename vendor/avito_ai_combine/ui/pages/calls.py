import json, threading
from avito_ai_combine.services.business_modules import BusinessModulesService
class CallsPage:
    def __init__(self,parent,ctk,runtime): self.rt=runtime; self.box=ctk.CTkTextbox(parent); self.box.pack(fill='both',expand=True); ctk.CTkButton(parent,text='SYNC CALLS',command=self.sync).pack(anchor='w',pady=8); self.refresh()
    def sync(self): threading.Thread(target=lambda:(BusinessModulesService(self.rt).sync_calls(),self.box.after(0,self.refresh)),daemon=True).start()
    def refresh(self): self.box.delete('1.0','end'); [self.box.insert('end',json.dumps(json.loads(r['data']),ensure_ascii=False,indent=2)+'\n\n') for r in self.rt.db.query('select data from calls order by id desc')]

import json, threading
from avito_ai_combine.services.business_modules import BusinessModulesService
class ListingsPage:
    def __init__(self,parent,ctk,runtime):
        self.rt=runtime; self.ctk=ctk; self.frame=ctk.CTkFrame(parent,fg_color='transparent'); self.frame.pack(fill='both',expand=True)
        ctk.CTkButton(self.frame,text='SYNC LISTINGS + STATS',command=self.sync).pack(anchor='w'); self.box=ctk.CTkTextbox(self.frame); self.box.pack(fill='both',expand=True,pady=10); self.refresh()
    def refresh(self):
        rows=self.rt.db.query('select external_id,data from listings order by id desc'); self.box.delete('1.0','end')
        for r in rows:
            x=json.loads(r['data']); self.box.insert('end',f"#{r['external_id']}  {x.get('title','')}  | {x.get('status','')} | {x.get('price','')}\n")
    def sync(self):
        def w():
            try: BusinessModulesService(self.rt).sync_listings(); BusinessModulesService(self.rt).sync_stats(); self.frame.after(0,self.refresh)
            except Exception as e: self.frame.after(0,lambda:self.box.insert('end',f'ERROR {e}\n'))
        threading.Thread(target=w,daemon=True).start()

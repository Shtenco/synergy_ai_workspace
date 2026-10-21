import threading
from avito_ai_combine.services.business_modules import BusinessModulesService
class AutoloadPage:
    def __init__(self,parent,ctk,runtime):
        self.rt=runtime; self.box=ctk.CTkTextbox(parent); self.box.pack(fill='both',expand=True); ctk.CTkButton(parent,text='CHECK AUTOLOAD V4',command=self.check).pack(anchor='w',pady=8)
    def check(self):
        def w():
            try: r=BusinessModulesService(self.rt).autoload_status(); self.box.after(0,lambda:self._show(r))
            except Exception as e: self.box.after(0,lambda:self._show({'error':str(e)}))
        threading.Thread(target=w,daemon=True).start()
    def _show(self,r): self.box.delete('1.0','end'); self.box.insert('end',str(r))

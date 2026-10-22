import threading
from avito_ai_combine.services.business_modules import BusinessModulesService
class PromotionPage:
    def __init__(self,parent,ctk,runtime):
        self.rt=runtime; self.entry=ctk.CTkEntry(parent,placeholder_text='Item ID'); self.entry.pack(anchor='w',fill='x'); ctk.CTkButton(parent,text='GET SERVICES + FORECAST (NO SPEND)',command=self.observe).pack(anchor='w',pady=8); self.box=ctk.CTkTextbox(parent); self.box.pack(fill='both',expand=True)
    def observe(self):
        def w():
            try: r=BusinessModulesService(self.rt).promotion_observe([int(self.entry.get())]); self.box.after(0,lambda:self._show(r))
            except Exception as e: self.box.after(0,lambda:self._show({'error':str(e)}))
        threading.Thread(target=w,daemon=True).start()
    def _show(self,r): self.box.delete('1.0','end'); self.box.insert('end',str(r))

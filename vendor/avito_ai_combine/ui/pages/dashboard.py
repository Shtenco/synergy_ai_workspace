import threading
from avito_ai_combine.services.business_modules import BusinessModulesService
class DashboardPage:
    def __init__(self,parent,ctk,runtime):
        self.rt=runtime; self.ctk=ctk; self.frame=ctk.CTkFrame(parent,fg_color='transparent'); self.frame.pack(fill='both',expand=True)
        top=ctk.CTkFrame(self.frame,fg_color='transparent'); top.pack(fill='x'); ctk.CTkButton(top,text='SYNC BUSINESS DATA',command=self.sync).pack(side='left'); self.status=ctk.CTkLabel(top,text='SQLite dashboard'); self.status.pack(side='left',padx=12)
        self.cards=ctk.CTkFrame(self.frame,fg_color='transparent'); self.cards.pack(fill='both',expand=True,pady=12); self.refresh()
    def refresh(self):
        for w in self.cards.winfo_children(): w.destroy()
        d=BusinessModulesService(self.rt).dashboard(); vals=[('Active listings',d['active_listings']),('Views',d['views']),('Contacts',d['contacts']),('Favorites',d['favorites']),('Spend',round(d['spend'],2)),('Contact rate',f"{d['contact_rate']*100:.2f}%" if d['contact_rate'] is not None else '—'),('CPL',round(d['cpl'],2) if d['cpl'] is not None else '—'),('Reviews',d['reviews']),('Calls',d['calls'])]
        self.cards.grid_columnconfigure((0,1,2),weight=1)
        for i,(k,v) in enumerate(vals):
            c=self.ctk.CTkFrame(self.cards); c.grid(row=i//3,column=i%3,sticky='nsew',padx=6,pady=6); self.ctk.CTkLabel(c,text=k,text_color='#aaa').pack(anchor='w',padx=16,pady=(15,2)); self.ctk.CTkLabel(c,text=str(v),font=self.ctk.CTkFont(size=24,weight='bold')).pack(anchor='w',padx=16,pady=(0,15))
    def sync(self):
        def work():
            try: r=BusinessModulesService(self.rt).sync_all(); self.frame.after(0,lambda:(self.status.configure(text=str(r)),self.refresh()))
            except Exception as e: self.frame.after(0,lambda:self.status.configure(text=f'ERROR: {e}'))
        threading.Thread(target=work,daemon=True).start()

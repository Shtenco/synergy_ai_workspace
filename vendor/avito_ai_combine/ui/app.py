from pathlib import Path
from avito_ai_combine.ui.navigation import PAGES
from avito_ai_combine.ui.state import AppState
from avito_ai_combine.app.bootstrap import build_local_runtime
class AvitoAICombineApp:
    def __init__(self,data_dir=None): self.state=AppState(); self.pages=PAGES; self.data_dir=Path(data_dir or (Path.home()/'.avito_ai_combine')); self.runtime=None
    def health(self): return {'product':'AVITO AI COMBINE','pages':len(self.pages),'legacy_socials':False}
    def run(self):
        import customtkinter as ctk
        from avito_ai_combine.ui.pages.connection import ConnectionPage
        from avito_ai_combine.ui.pages.messages import MessagesPage
        from avito_ai_combine.ui.pages.dashboard import DashboardPage
        from avito_ai_combine.ui.pages.listings import ListingsPage
        from avito_ai_combine.ui.pages.analytics import AnalyticsPage
        from avito_ai_combine.ui.pages.autoload import AutoloadPage
        from avito_ai_combine.ui.pages.reviews import ReviewsPage
        from avito_ai_combine.ui.pages.calls import CallsPage
        from avito_ai_combine.ui.pages.promotion import PromotionPage
        from avito_ai_combine.ui.pages.automation import AutomationPage
        from avito_ai_combine.ui.pages.ai_center import AICenterPage
        self.runtime=build_local_runtime(self.data_dir)
        ctk.set_appearance_mode('dark'); root=ctk.CTk(); root.title('AVITO AI COMBINE'); root.geometry('1500x920'); root.minsize(1150,720)
        root.grid_columnconfigure(1,weight=1); root.grid_rowconfigure(1,weight=1)
        head=ctk.CTkFrame(root,height=70,corner_radius=0); head.grid(row=0,column=0,columnspan=2,sticky='nsew')
        ctk.CTkLabel(head,text='AVITO AI COMBINE',font=ctk.CTkFont(size=24,weight='bold')).pack(side='left',padx=24,pady=18)
        api_state=ctk.CTkLabel(head,text='API: OFFLINE   •   WEBHOOK: LOCAL OFF   •   AI: COPILOT',text_color='#b7b7b7'); api_state.pack(side='right',padx=24)
        nav=ctk.CTkScrollableFrame(root,width=235,corner_radius=0); nav.grid(row=1,column=0,sticky='nsew')
        content=ctk.CTkFrame(root,corner_radius=0); content.grid(row=1,column=1,sticky='nsew'); content.grid_columnconfigure(0,weight=1); content.grid_rowconfigure(1,weight=1)
        title=ctk.CTkLabel(content,text='Dashboard',font=ctk.CTkFont(size=28,weight='bold')); title.grid(row=0,column=0,sticky='w',padx=28,pady=(25,12))
        body=ctk.CTkFrame(content); body.grid(row=1,column=0,sticky='nsew',padx=28,pady=(0,28)); body.grid_columnconfigure(0,weight=1); body.grid_rowconfigure(0,weight=1)
        def clear():
            for w in body.winfo_children(): w.destroy()
        def set_api(ok): api_state.configure(text=('API: CONNECTED' if ok else 'API: ERROR')+'   •   WEBHOOK: LOCAL OFF   •   AI: COPILOT')
        def show(name):
            title.configure(text=name); clear()
            if name=='Connection': ConnectionPage(body,ctk,self.runtime,set_api); return
            if name=='Messages': MessagesPage(body,ctk,self.runtime); return
            pages={'Dashboard':DashboardPage,'Listings':ListingsPage,'Analytics':AnalyticsPage,'Autoload':AutoloadPage,'Reviews':ReviewsPage,'Calls':CallsPage,'Promotion':PromotionPage,'Automation':AutomationPage,'AI Center':AICenterPage}
            if name in pages: pages[name](body,ctk,self.runtime); return
            ctk.CTkLabel(body,text=f'{name}\n\nModule ready for the next domain-specific live pass.',font=ctk.CTkFont(size=18),justify='left').pack(anchor='nw',padx=24,pady=24)
        for name in PAGES: ctk.CTkButton(nav,text=name,anchor='w',height=38,fg_color='transparent',hover_color='#7a1717',command=lambda n=name:show(n)).pack(fill='x',padx=8,pady=3)
        show('Dashboard'); root.mainloop()

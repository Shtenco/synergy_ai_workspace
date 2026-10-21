from avito_ai_combine.services.business_modules import BusinessModulesService
class AnalyticsPage:
    def __init__(self,parent,ctk,runtime):
        d=BusinessModulesService(runtime).dashboard(); box=ctk.CTkTextbox(parent); box.pack(fill='both',expand=True); box.insert('end','AVITO ANALYTICS\n\n'+ '\n'.join(f'{k}: {v}' for k,v in d.items())); box.configure(state='disabled')

from avito_ai_combine.services.autopilot import AutopilotService
class AICenterPage:
    def __init__(self,parent,ctk,runtime):
        self.rt=runtime; ctk.CTkLabel(parent,text='AI AUTOPILOT CONTROL',font=ctk.CTkFont(size=22,weight='bold')).pack(anchor='w'); self.mode=ctk.CTkOptionMenu(parent,values=['OFF','ADVISER','COPILOT','AUTOPILOT'],command=self.set_mode); self.mode.set(runtime.config.autonomy_mode); self.mode.pack(anchor='w',pady=12); self.status=ctk.CTkLabel(parent,text='External writes remain policy-gated. Promotion spend requires approval/limit.'); self.status.pack(anchor='w')
    def set_mode(self,value): self.rt.config.autonomy_mode=value; self.rt.config.save(self.rt.data_dir/'config.json'); self.status.configure(text=f'Autonomy mode: {value}')

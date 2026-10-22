import json
from avito_ai_combine.services.rule_engine import PersistentRuleEngine
from avito_ai_combine.automation.policies import AutonomyMode
class AutomationPage:
    def __init__(self,parent,ctk,runtime):
        self.rt=runtime; self.eng=PersistentRuleEngine(runtime); self.frame=ctk.CTkFrame(parent,fg_color='transparent'); self.frame.pack(fill='both',expand=True)
        ctk.CTkLabel(self.frame,text='WHEN lead.score.changed IF score >= 70 THEN create_task').pack(anchor='w'); ctk.CTkButton(self.frame,text='ADD HOT LEAD RULE',command=self.add).pack(anchor='w',pady=8); self.box=ctk.CTkTextbox(self.frame); self.box.pack(fill='both',expand=True); self.refresh()
    def add(self): self.eng.create_rule('Hot lead follow-up','lead.score.changed',{'min_score':70},{'type':'create_task','title':'Связаться с горячим лидом'},AutonomyMode.AUTOPILOT); self.refresh()
    def refresh(self): self.box.delete('1.0','end'); [self.box.insert('end',json.dumps(json.loads(r['data']),ensure_ascii=False,indent=2)+'\n\n') for r in self.rt.db.query('select data from automation_rules order by id desc')]

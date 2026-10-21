import threading
class MessagesPage:
    def __init__(self,parent,ctk,runtime):
        from avito_ai_combine.services.messaging import PersistentMessagingService
        self.ctk=ctk; self.rt=runtime; self.service=PersistentMessagingService(runtime); self.selected=None
        self.frame=ctk.CTkFrame(parent); self.frame.pack(fill='both',expand=True); self.frame.grid_columnconfigure(1,weight=1); self.frame.grid_columnconfigure(2,weight=1); self.frame.grid_rowconfigure(1,weight=1)
        bar=ctk.CTkFrame(self.frame); bar.grid(row=0,column=0,columnspan=3,sticky='ew',padx=10,pady=10)
        ctk.CTkButton(bar,text='СИНХРОНИЗИРОВАТЬ AVITO',command=self.sync).pack(side='left',padx=8,pady=8)
        self.status=ctk.CTkLabel(bar,text='SQLite inbox'); self.status.pack(side='left',padx=10)
        self.chats=ctk.CTkScrollableFrame(self.frame,width=260); self.chats.grid(row=1,column=0,sticky='nsew',padx=(10,5),pady=(0,10))
        self.conv=ctk.CTkScrollableFrame(self.frame); self.conv.grid(row=1,column=1,sticky='nsew',padx=5,pady=(0,10))
        right=ctk.CTkFrame(self.frame,width=330); right.grid(row=1,column=2,sticky='nsew',padx=(5,10),pady=(0,10)); right.grid_rowconfigure(2,weight=1); right.grid_columnconfigure(0,weight=1)
        self.lead=ctk.CTkLabel(right,text='Лид не выбран',justify='left',anchor='nw'); self.lead.grid(row=0,column=0,sticky='ew',padx=12,pady=12)
        self.profile=ctk.CTkOptionMenu(right,values=['visa_residence','real_estate','photo_content','ai_automation','general']); self.profile.grid(row=1,column=0,sticky='ew',padx=12,pady=6)
        self.draft=ctk.CTkTextbox(right); self.draft.grid(row=2,column=0,sticky='nsew',padx=12,pady=6)
        ctk.CTkButton(right,text='AI DRAFT',command=self.ai_draft).grid(row=3,column=0,sticky='ew',padx=12,pady=6)
        ctk.CTkButton(right,text='ОТПРАВИТЬ В AVITO',command=self.send,fg_color='#8b1d1d').grid(row=4,column=0,sticky='ew',padx=12,pady=(6,12))
        self.rt.events.subscribe('avito.webhook',lambda payload:self.frame.after(0,self._on_webhook))
        self.refresh_local()
    def _on_webhook(self):
        self.status.configure(text='Realtime: новое событие Avito')
        self.refresh_local()
        if self.selected:self.open_chat(self.selected)
    def sync(self):
        self.status.configure(text='Синхронизация...')
        def work():
            try:
                r=self.service.sync(); self.frame.after(0,lambda:self._after_sync(r))
            except Exception as e: self.frame.after(0,lambda:self.status.configure(text=f'Ошибка: {type(e).__name__}: {e}'))
        threading.Thread(target=work,daemon=True).start()
    def _after_sync(self,r): self.status.configure(text=f"Чаты {r['chats']} • сообщения +{r['messages']} • новые лиды {r['leads']}"); self.refresh_local()
    def refresh_local(self):
        for w in self.chats.winfo_children(): w.destroy()
        for ch in self.service.list_local_chats(): self.ctk.CTkButton(self.chats,text=ch['title'],anchor='w',fg_color='transparent',command=lambda c=ch:self.open_chat(c['chat_id'])).pack(fill='x',pady=2)
    def open_chat(self,chat_id):
        self.selected=chat_id
        for w in self.conv.winfo_children(): w.destroy()
        for m in self.service.list_local_messages(chat_id): self.ctk.CTkLabel(self.conv,text=m['text'] or '[media]',wraplength=430,justify='left').pack(anchor='w',padx=10,pady=7)
        lead=self.service.get_lead_for_chat(chat_id); self.lead.configure(text=('CRM LEAD\n'+ '\n'.join(f'{k}: {v}' for k,v in (lead or {}).items())) if lead else 'CRM lead: нет')
    def ai_draft(self):
        if not self.selected:return
        r=self.service.draft_reply(self.selected,self.profile.get()); self.draft.delete('1.0','end'); self.draft.insert('1.0',r.get('text') or f"AI требует участия оператора: {r.get('reason')}")
    def send(self):
        if not self.selected:return
        text=self.draft.get('1.0','end').strip()
        if not text:return
        self.status.configure(text='Отправка...')
        def work():
            try: self.service.send_text(self.selected,text); self.frame.after(0,lambda:self.status.configure(text='✓ Отправлено в Avito'))
            except Exception as e: self.frame.after(0,lambda:self.status.configure(text=f'Ошибка отправки: {e}'))
        threading.Thread(target=work,daemon=True).start()

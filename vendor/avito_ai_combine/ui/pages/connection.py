import threading
class ConnectionPage:
    def __init__(self,parent,ctk,runtime,on_status=None):
        from avito_ai_combine.services.connection import ConnectionManager
        self.ctk=ctk; self.rt=runtime; self.manager=ConnectionManager(runtime); self.on_status=on_status or (lambda *_:None)
        self.frame=ctk.CTkFrame(parent); self.frame.pack(fill='both',expand=True,padx=18,pady=18)
        ctk.CTkLabel(self.frame,text='Подключение Avito API',font=ctk.CTkFont(size=22,weight='bold')).pack(anchor='w',padx=18,pady=(18,4))
        ctk.CTkLabel(self.frame,text='Client ID хранится в config.json, Client Secret - только в зашифрованном vault.',text_color='#aaa').pack(anchor='w',padx=18,pady=(0,16))
        self.cid=ctk.CTkEntry(self.frame,placeholder_text='Client ID',height=42); self.cid.pack(fill='x',padx=18,pady=6); self.cid.insert(0,runtime.config.client_id or '')
        self.secret=ctk.CTkEntry(self.frame,placeholder_text='Client Secret',show='•',height=42); self.secret.pack(fill='x',padx=18,pady=6)
        if runtime.vault.get('client_secret'): self.secret.insert(0,runtime.vault.get('client_secret'))
        self.webhook=ctk.CTkEntry(self.frame,placeholder_text='Public HTTPS Webhook URL, например https://domain.ru/avito/webhook',height=42); self.webhook.pack(fill='x',padx=18,pady=6); self.webhook.insert(0,runtime.config.webhook_url or '')
        self.status=ctk.CTkLabel(self.frame,text='Не проверено',justify='left'); self.status.pack(anchor='w',padx=18,pady=14)
        row=ctk.CTkFrame(self.frame,fg_color='transparent'); row.pack(fill='x',padx=18,pady=6)
        ctk.CTkButton(row,text='СОХРАНИТЬ',command=self.save).pack(side='left',padx=(0,8))
        ctk.CTkButton(row,text='API CHECK',command=self.check,fg_color='#8b1d1d',hover_color='#a72525').pack(side='left')
        ctk.CTkButton(row,text='START LOCAL WEBHOOK',command=self.start_webhook).pack(side='left',padx=8)
        ctk.CTkButton(row,text='SUBSCRIBE URL',command=self.subscribe).pack(side='left')
    def save(self):
        try: self.rt.config.webhook_url=self.webhook.get().strip(); self.rt.config.save(self.rt.data_dir/'config.json'); self.manager.save_credentials(self.cid.get(),self.secret.get()); self.status.configure(text='✓ Credentials сохранены локально и зашифрованы')
        except Exception as e: self.status.configure(text=f'Ошибка сохранения: {e}')
    def check(self):
        self.save(); self.status.configure(text='Проверяю Avito API...')
        def work():
            try:
                r=self.manager.check_live(); caps=', '.join(k for k,v in r['capabilities'].items() if v) or 'scopes не заявлены токеном'
                txt=f"✓ API CONNECTED\nAccount ID: {self.rt.account_id}\nАккаунт: {r['account'].get('name') or r['account'].get('email') or '-'}\nCapabilities: {caps}"
                self.frame.after(0,lambda:self._set(txt,True))
            except Exception as e: self.frame.after(0,lambda:self._set(f'✕ API CHECK: {type(e).__name__}: {e}',False))
        threading.Thread(target=work,daemon=True).start()
    def _set(self,text,ok): self.status.configure(text=text); self.on_status(ok)

    def start_webhook(self):
        try:
            from avito_ai_combine.webhooks.server import WebhookServer
            if getattr(self,'server',None): self.server.stop()
            self.server=WebhookServer(self.rt.webhook_handler,host='127.0.0.1',port=8765).start()
            self.status.configure(text=f'✓ Local webhook: http://127.0.0.1:{self.server.port}/avito/webhook\nДля Avito нужен публичный HTTPS URL, который проксирует сюда.')
        except Exception as e:self.status.configure(text=f'Webhook error: {e}')
    def subscribe(self):
        url=self.webhook.get().strip()
        if not url.startswith('https://'):
            self.status.configure(text='Webhook subscription требует публичный HTTPS URL.'); return
        if not self.rt.token or not self.rt.account_id:
            self.status.configure(text='Сначала выполните API CHECK.'); return
        def work():
            try:
                from avito_ai_combine.avito.messenger import MessengerClient
                r=MessengerClient(self.rt.transport,self.rt.token.access_token,self.rt.account_id).subscribe_webhook(url)
                self.frame.after(0,lambda:self.status.configure(text=f'✓ Webhook subscription отправлена: {url}'))
            except Exception as e:self.frame.after(0,lambda:self.status.configure(text=f'Webhook subscribe error: {e}'))
        threading.Thread(target=work,daemon=True).start()

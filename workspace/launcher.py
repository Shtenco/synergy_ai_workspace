"""SYNERGY AI WORKSPACE - local orchestration shell, no privileged automation."""
from __future__ import annotations
import json, os, subprocess, sys, threading, tkinter as tk, urllib.request
from pathlib import Path
from tkinter import ttk, messagebox
ROOT=Path(__file__).resolve().parents[1]
VENDOR=ROOT/'vendor'
AUTOPILOT=VENDOR/'synergy_agi_autopilot'
SMM=VENDOR/'synergy.github.io'/'smm'
AVITO=VENDOR/'avito_ai_combine'
API='http://127.0.0.1:8120/health'
COLORS={'bg':'#0c0e13','side':'#13161d','panel':'#191c25','text':'#f3f4f6','muted':'#9ca3af','red':'#e64455','border':'#343741'}
SECTIONS=['Overview','AI AUTOPILOT','AI SMM','AI AVITO','Lead OS','Integration status']
class Shell:
 def __init__(self):
  self.app=tk.Tk(); self.app.title('SYNERGY AI WORKSPACE • Integration Preview');self.app.geometry('1240x780');self.app.minsize(920,600);self.app.configure(bg=COLORS['bg'])
  self.side=tk.Frame(self.app,bg=COLORS['side'],width=230);self.side.pack(side='left',fill='y');self.side.pack_propagate(False)
  tk.Label(self.side,text='SYNERGY',font=('Segoe UI',25,'bold'),fg=COLORS['red'],bg=COLORS['side']).pack(anchor='w',padx=18,pady=(28,0))
  tk.Label(self.side,text='AI WORKSPACE  /  INTEGRATION',font=('Segoe UI',9),fg=COLORS['muted'],bg=COLORS['side']).pack(anchor='w',padx=19,pady=(0,30))
  for s in SECTIONS:
   tk.Button(self.side,text=s,anchor='w',relief='flat',bd=0,padx=18,pady=13,font=('Segoe UI',11),fg=COLORS['text'],bg=COLORS['side'],activebackground=COLORS['panel'],activeforeground=COLORS['red'],command=lambda k=s:self.page(k)).pack(fill='x',pady=2)
  self.body=tk.Frame(self.app,bg=COLORS['bg']);self.body.pack(side='left',fill='both',expand=True)
  self.page('Overview')
 def text(self,t,size=12,muted=False):tk.Label(self.body,text=t,fg=COLORS['muted'] if muted else COLORS['text'],bg=COLORS['bg'],font=('Segoe UI',size),justify='left',anchor='w',wraplength=840).pack(fill='x',padx=30,pady=9)
 def btn(self,title,callback):tk.Button(self.body,text=title,command=callback,fg='white',bg='#912b38',activebackground=COLORS['red'],relief='flat',bd=0,font=('Segoe UI',11,'bold'),padx=20,pady=11).pack(anchor='w',padx=30,pady=10)
 def page(self,section):
  for child in self.body.winfo_children():child.destroy()
  self.text(section,25)
  if section=='Overview':
   self.text('Единая точка входа в исходные проекты AUTOPILOT / SMM / AVITO.',14)
   self.text('Оригинальный архив Avito сохранён полностью. AUTOPILOT и SMM подключаются при импорте Git-репозиториев. Запуск внешних операций требует отдельной авторизации и разрешений.',11,True)
   self.btn('Открыть AI AVITO',self.avito)
   self.btn('Проверить интеграции',lambda:self.page('Integration status'))
  elif section=='AI AVITO':
   self.text('Оригинальный AVITO AI COMBINE V1 • customtkinter • Python',14)
   self.text(f'Исходники: {AVITO}',10,True)
   self.btn('Запустить настоящий Avito Desktop',self.avito)
   self.text('Для запуска GUI нужны установленные зависимости cryptography и customtkinter. API-ключи не сохраняются в этой оболочке.',11,True)
  elif section=='AI SMM':
   self.text('Оригинальные кабинеты из Shtenco/synergy.github.io/smm',14)
   if SMM.exists():
    for name in ['index.html','workspaces.html','studio.html','lead-radar.html','ai-studio.html','caseflow.html','cabinet.html']:
     if (SMM/name).exists():self.btn('Открыть '+name,lambda n=name:self.open_file(SMM/n))
   else:self.text('Исходный каталог ещё не импортирован. Выполните import_original_sources.py в среде с GitHub.',11,True)
  elif section=='AI AUTOPILOT':
   self.text('Оригинальный Rust/Tauri Desktop и Python capability runtime',14)
   self.text('Источники: integration/synergy-ai-autopilot-v1 и feat/capability-runtime-v1.',11,True)
   if AUTOPILOT.exists(): self.text('Git-репозиторий найден локально.',11)
   else:self.text('Оригинальный Git-репозиторий ещё не импортирован.',11,True)
   self.btn('Проверить локальный runtime API',self.check_api)
  elif section=='Lead OS':
   self.text('Отдельный Python Lead OS: Shtenco/synergy_lead_search_engline',14)
   self.text('API/CRM интегрируются только после проверки авторизации и контрактов. В этом прототипе внешний сбор персональных данных и отправка сообщений отключены.',11,True)
  else:
   for k,p in [('AVITO (в архиве)',AVITO),('AUTOPILOT (Git)',AUTOPILOT),('SMM (Git)',SMM),('Lead OS (Git)',VENDOR/'synergy_lead_search_engline')]:self.text(('✓' if p.exists() else '○')+'  '+k+'  —  '+('источники присутствуют' if p.exists() else 'ожидают импорта'),11)
   self.btn('Проверить runtime',self.check_api)
 def open_file(self,path):
  import webbrowser
  webbrowser.open(path.resolve().as_uri())
 def check_api(self):
  def go():
   try:
    with urllib.request.urlopen(API,timeout=2) as f: result=f.read(1600).decode('utf-8','replace')
    self.app.after(0,lambda:messagebox.showinfo('AUTOPILOT API',result))
   except Exception as ex:self.app.after(0,lambda:messagebox.showwarning('AUTOPILOT API','Нет подтверждённого runtime на 127.0.0.1:8120. '+str(ex)))
  threading.Thread(target=go,daemon=True).start()
 def avito(self):
  if not AVITO.exists():messagebox.showerror('Missing files','Avito original source not found');return
  env=os.environ.copy();env['PYTHONPATH']=str(VENDOR)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
  try:subprocess.Popen([sys.executable,'-m','avito_ai_combine.main'],cwd=VENDOR,env=env)
  except Exception as e:messagebox.showerror('Launch error',str(e))
 def run(self):self.app.mainloop()
if __name__=='__main__':Shell().run()

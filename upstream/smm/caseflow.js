"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const ENDPOINT = '/api/v2/smm/caseflow';
  let selected = null;
  let filter = 'all';
  const form = $('intake-form');
  const state = $('api-state');
  const setState = (text, ok) => {state.textContent=text; state.classList.toggle('ok',!!ok)};
  async function api(path, options={}) {
    const res=await fetch(ENDPOINT+path,{credentials:'same-origin',headers:{'Accept':'application/json', ...(options.body?{'Content-Type':'application/json'}:{} )},...options});
    let data;try{data=await res.json()}catch{data={detail:'Некорректный ответ сервера'}};
    if(!res.ok)throw Object.assign(new Error(typeof data.detail==='string'?data.detail:`HTTP ${res.status}`),{status:res.status});
    return data;
  }
  function tag(parent,name,text,cls=''){
    const e=document.createElement(name);e.textContent=String(text??'');if(cls)e.className=cls;parent.appendChild(e);return e;
  }
  function msg(id,value,error=false){const e=$(id);e.textContent=value;e.classList.toggle('error',error);e.classList.toggle('good',!error)}
  async function session(){
    try{const r=await fetch('/api/v1/session',{credentials:'same-origin'});const d=await r.json();$('auth-panel').hidden=!!d.authenticated;setState(d.authenticated?'● OPERATOR / AUTHENTICATED':'● AUTH REQUIRED',d.authenticated);return !!d.authenticated}
    catch {setState('● API UNAVAILABLE',false);$('auth-panel').hidden=false;return false}
  }
  async function refresh(){
    if(!await session())return;
    try{
      const [counts,list]=await Promise.all([api('/metrics'),api('/cases?status='+encodeURIComponent(filter)+'&limit=100')]);
      for(const s of ['candidate','qualified','dismissed'])$('metric-'+s).textContent=counts.cases[s]||0;
      $('metric-drafts').textContent=counts.drafts;
      const container=$('case-list');container.replaceChildren();
      if(!list.cases.length){tag(container,'div','Пока нет карточек с этим статусом. Начни с формы слева.','empty');return}
      for(const item of list.cases){
        const b=tag(container,'button','','case-card');b.type='button';b.setAttribute('aria-label','Открыть '+item.summary);b.classList.toggle('selected',selected?.id===item.id);
        tag(b,'span',item.platform.toUpperCase()+'  /  '+item.priority+' · '+item.score,'small');tag(b,'strong',item.summary);tag(b,'span',item.status+'  ·  '+item.created_utc.slice(0,16).replace('T',' '),'meta');b.addEventListener('click',()=>load(item.id));
      }
    }catch(e){if(e.status===401){await session()}tag($('case-list'),'div',`Не удалось загрузить: ${e.message}`,'empty')}
  }
  async function load(id){
    try{
      const data=await api('/cases/'+encodeURIComponent(id));selected=data.case;
      const pane=$('case-detail');pane.replaceChildren();
      tag(pane,'h3',data.case.summary);
      for(const [k,v] of [['Ссылка / источник',data.case.source_ref],['Канал',data.case.platform],['Основание',data.case.lawful_basis],['Python Lead Radar',`${data.case.priority} / ${data.case.score} баллов`],['Причины оценки',data.case.reasons.join(', ')||'Нет дополнительных сигналов'],['Этап',data.case.status]]){
        const row=tag(pane,'p','');tag(row,'b',k+': ');tag(row,'span',v);
      }
      if(!data.case.outreach_allowed)tag(pane,'p','Публичное исследование не даёт разрешения писать этому человеку.','feedback');
      $('selected-status').textContent=data.case.priority+' · '+data.case.status;
      $('review-form').hidden=false;
      $('draft-form').hidden=!(data.case.status==='qualified'&&data.case.outreach_allowed);
      const history=$('audit-log');history.replaceChildren();
      for(const ev of data.events){const item=tag(history,'div','','audit-item');tag(item,'b',ev.action);tag(item,'small',ev.created_utc.slice(0,19).replace('T',' ')+' · версия '+ev.version);if(ev.note)tag(item,'div',ev.note)}
      for(const draft of data.drafts){const item=tag(history,'div','','audit-item');tag(item,'b','Сохранён черновик · без отправки');tag(item,'small',draft.created_utc.slice(0,19).replace('T',' '));tag(item,'p',draft.body)}
      await refresh();
    }catch(e){msg('intake-status',e.message,true)}
  }
  $('login-form').addEventListener('submit',async ev=>{
    ev.preventDefault();const p=$('password').value;
    try{const r=await fetch('/api/v1/auth/login',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:p})});if(!r.ok)throw new Error('Вход не выполнен ('+r.status+')');$('password').value='';await refresh()}
    catch(e){setState('● '+e.message,false)}
  });
  form.addEventListener('submit',async ev=>{
    ev.preventDefault();const fd=new FormData(form);const json={};for(const [k,v] of fd)json[k]=v;json.authorized_to_process=fd.has('authorized_to_process');
    msg('intake-status','Обрабатываю данные оригинальным Python Lead Radar…');
    try{const data=await api('/cases',{method:'POST',body:JSON.stringify(json)});form.reset();msg('intake-status','Карточка сохранена: '+data.priority+' / '+data.score+' баллов. Источник зафиксирован, сырой текст не сохранён.');await refresh();await load(data.id)}
    catch(e){msg('intake-status',e.message,true)}
  });
  for(const el of document.querySelectorAll('.filter'))el.addEventListener('click',()=>{filter=el.dataset.filter;document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===el));refresh()});
  $('refresh').addEventListener('click',refresh);
  $('review-form').addEventListener('click',async ev=>{
    const b=ev.target.closest('button[data-action]');if(!b||!selected)return;
    ev.preventDefault();try{const d=await api('/cases/'+encodeURIComponent(selected.id)+'/review',{method:'POST',body:JSON.stringify({action:b.dataset.action,note:$('review-form').elements.note.value,expected_version:selected.version})});msg('intake-status','Решение сохранено: '+d.status);await load(selected.id)}catch(e){msg('intake-status',e.message+' — обновите карточку.',true)}
  });
  $('draft-form').addEventListener('submit',async ev=>{
    ev.preventDefault();if(!selected)return;
    try{const d=await api('/cases/'+encodeURIComponent(selected.id)+'/engagement-drafts',{method:'POST',body:JSON.stringify({body:ev.target.elements.body.value,confirmation:'PREPARE_DRAFT_ONLY'})});ev.target.reset();msg('intake-status','Черновик '+d.id+' сохранён. Сообщение НЕ отправлено.');await load(selected.id)}catch(e){msg('intake-status',e.message,true)}
  });
  refresh();
})();

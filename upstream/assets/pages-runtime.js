/* SYNERGY GitHub Pages: server API must be deployed separately. No secrets here. */
(function(){
  'use strict';
  const siteBase='/synergy.github.io/';
  const backend=''; /* Set only to an authorized HTTPS FastAPI origin after deployment */
  window.SYNERGY_PAGES={base:siteBase,backend:backend||null,staticHosting:true};
  const oldFetch=window.fetch.bind(window);
  function isApiPath(p){return /^\/(?:api\/|video\/api\/|advert\/api\/|market\/api\/|auth\/)/.test(p);}
  window.fetch=function(input,init){
    const raw=typeof input==='string'?input:(input instanceof URL?input.href:(input&&input.url)||'');
    let u;try{u=new URL(raw,location.href);}catch(e){return oldFetch(input,init);}
    if(u.origin!==location.origin || !isApiPath(u.pathname))return oldFetch(input,init);
    if(!backend){return Promise.resolve(new Response(JSON.stringify({detail:'Защищённый Python API ещё не развёрнут. GitHub Pages предоставляет только веб-интерфейс.',status:'backend_not_configured'}),{status:503,headers:{'content-type':'application/json; charset=utf-8'}}));}
    if(!/^https:\/\//i.test(backend))return Promise.reject(new Error('Backend requires HTTPS'));
    return oldFetch(backend.replace(/\/$/,'')+u.pathname+u.search,{...(init||{}),credentials:'include'});
  };
  document.addEventListener('DOMContentLoaded',function(){
    const el=document.createElement('div');
    el.id='syn-pages-status';
    el.setAttribute('role','status');
    el.innerHTML='<span class="syn-dot"></span><strong>SYNERGY WEB</strong><span>Публичный интерфейс · Python API не подключён</span>';
    document.body.appendChild(el);
    const st=document.createElement('style');st.textContent='#syn-pages-status{position:fixed;bottom:12px;left:12px;z-index:99999;display:flex;gap:8px;align-items:center;max-width:calc(100vw - 24px);border-radius:11px;padding:9px 13px;background:#09140ecf;color:#e6faed;border:1px solid #268d4b80;box-shadow:0 14px 32px #0009;backdrop-filter:blur(12px);font:11px/1.35 system-ui,sans-serif}#syn-pages-status strong{color:#00e664;font-size:10px;letter-spacing:.06em}#syn-pages-status .syn-dot{height:7px;width:7px;flex:0 0 7px;border-radius:50%;background:#e9b750}#syn-pages-status span:last-child{color:#c0d5c5}@media(max-width:460px){#syn-pages-status{font-size:9px;padding:7px 9px;bottom:8px;left:8px}}';
    document.head.appendChild(st);
  });
})();

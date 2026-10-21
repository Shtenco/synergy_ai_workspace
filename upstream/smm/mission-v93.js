/* Read-only, real runtime status. Never substitutes demonstration data for authenticated results. */
(()=>{'use strict';
const s=(id)=>document.getElementById(id);
async function get(path){let r=await fetch(path,{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);return r.json()}
function set(id,value,state='off',note){const x=s(id);if(!x)return;x.querySelector('strong').textContent=value;x.dataset.state=state;if(note)x.querySelector('p').textContent=note}
async function refresh(){const b=s('s93-refresh');b.disabled=true;b.textContent='ПРОВЕРЯЮ…';
  const result=await Promise.allSettled([get('/api/v1/health'),get('/api/v1/session'),get('/api/v2/smm/team/session'),get('/api/v1/modules')]);
  let [health,operator,team,modules]=result;
  if(health.status==='fulfilled')set('s93-gateway','API отвечает','ok','Версия: '+String(health.value.version||'не указана'));
  else set('s93-gateway','Нет связи','off','Сервер FastAPI недоступен');
  if(operator.status==='fulfilled')set('s93-operator',operator.value.authenticated?'Авторизован':'Нужен вход',operator.value.authenticated?'ok':'off',operator.value.authenticated?'Рабочая сессия оператора':'Войти можно в AI SMM / Lead Radar');
  else set('s93-operator','Не проверено','off','Ошибка запроса к сессии');
  if(team.status==='fulfilled')set('s93-team','Команда: вход есть','ok','Роль: '+String(team.value.user?.role||'неизвестно'));
  else set('s93-team','Нужен вход в Team','off','CaseFlow Team хранит данные отдельно');
  if(modules.status==='fulfilled')set('s93-catalog',String(modules.value.modules?.length??'—')+' модулей','ok','Реестр не подтверждает внешние интеграции');
  else set('s93-catalog','Нет данных','off','Каталог API недоступен');
  s('s93-last').textContent='Проверка выполнена: '+new Date().toLocaleTimeString('ru-RU');b.disabled=false;b.textContent='ОБНОВИТЬ СТАТУС ↻';
}
s('s93-refresh')?.addEventListener('click',refresh);refresh();
})();

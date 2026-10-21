import json
from datetime import date, timedelta
from avito_ai_combine.avito.listings import ListingsClient
from avito_ai_combine.avito.stats import StatsClient
from avito_ai_combine.avito.reviews import ReviewsClient
from avito_ai_combine.avito.calls import CallsClient
from avito_ai_combine.avito.autoload import AutoloadClient
from avito_ai_combine.avito.promotion import PromotionClient

class BusinessModulesService:
    def __init__(self, runtime): self.rt=runtime
    @property
    def token(self): return self.rt.token.access_token
    @staticmethod
    def _items(payload,*keys):
        cur=payload
        for k in keys:
            if isinstance(cur,dict): cur=cur.get(k,cur)
        if isinstance(cur,list): return cur
        if isinstance(cur,dict):
            for k in ('resources','items','reviews','calls','uploads','result'):
                if isinstance(cur.get(k),list): return cur[k]
        return []
    def _upsert(self,table,external_id,data):
        aid=str(self.rt.account_id)
        blob=json.dumps(data,ensure_ascii=False)
        rows=self.rt.db.query(f'select id from {table} where external_id=? and account_id=?',(str(external_id),aid))
        if rows: self.rt.db.execute(f'update {table} set data=? where id=?',(blob,rows[0]['id']))
        else: self.rt.db.execute(f'insert into {table}(external_id,account_id,data) values(?,?,?)',(str(external_id),aid,blob))
    def sync_listings(self):
        rows=self._items(ListingsClient(self.rt.transport,self.token).list())
        for x in rows: self._upsert('listings',x.get('id') or x.get('itemId'),x)
        return len(rows)
    def sync_stats(self):
        ids=[int(r['external_id']) for r in self.rt.db.query('select external_id from listings where account_id=?',(str(self.rt.account_id),)) if str(r['external_id']).isdigit()]
        if not ids: return 0
        today=date.today(); payload=StatsClient(self.rt.transport,self.token,self.rt.account_id).items(ids,str(today-timedelta(days=30)),str(today))
        rows=self._items(payload,'result','items')
        for x in rows: self._upsert('listing_stats_daily',x.get('itemId') or x.get('id'),x)
        return len(rows)
    def sync_reviews(self):
        rows=self._items(ReviewsClient(self.rt.transport,self.token).list())
        for x in rows: self._upsert('reviews',x.get('id'),x)
        return len(rows)
    def sync_calls(self):
        payload={'dateFrom':str(date.today()-timedelta(days=30)),'dateTo':str(date.today())}
        rows=self._items(CallsClient(self.rt.transport,self.token,self.rt.account_id).stats(payload))
        for x in rows: self._upsert('calls',x.get('id') or x.get('callId'),x)
        return len(rows)
    def sync_all(self):
        a=self.sync_listings(); b=self.sync_stats(); c=self.sync_reviews(); d=self.sync_calls()
        return {'listings':a,'stats':b,'reviews':c,'calls':d}
    def dashboard(self):
        listings=[json.loads(r['data']) for r in self.rt.db.query('select data from listings where account_id=?',(str(self.rt.account_id),))]
        stats=[json.loads(r['data']) for r in self.rt.db.query('select data from listing_stats_daily where account_id=?',(str(self.rt.account_id),))]
        views=sum(int(x.get('views',0) or 0) for x in stats); contacts=sum(int(x.get('contacts',0) or 0) for x in stats)
        favorites=sum(int(x.get('favorites',0) or 0) for x in stats); spend=sum(float(x.get('spending',x.get('spend',0)) or 0) for x in stats)
        return {'active_listings':sum(1 for x in listings if x.get('status')=='active'),'views':views,'contacts':contacts,'favorites':favorites,'spend':spend,'contact_rate':contacts/views if views else None,'cpl':spend/contacts if contacts else None,'reviews':self.rt.db.scalar('select count(*) from reviews where account_id=?',(str(self.rt.account_id),)) or 0,'calls':self.rt.db.scalar('select count(*) from calls where account_id=?',(str(self.rt.account_id),)) or 0}
    def autoload_status(self):
        c=AutoloadClient(self.rt.transport,self.token)
        return {'current':c.current(),'history':c.uploads()}
    def promotion_observe(self,item_ids):
        c=PromotionClient(self.rt.transport,self.token)
        return {'services':c.services(item_ids),'forecasts':c.forecasts({'itemIds':item_ids})}

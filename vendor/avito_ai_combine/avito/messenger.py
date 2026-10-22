class MessengerClient:
    def __init__(self,t,token,user_id): self.t=t; self.token=token; self.user_id=user_id
    def list_chats(self,**params): return self.t.request('GET',f'/messenger/v2/accounts/{self.user_id}/chats',token=self.token,params=params or None)
    def get_chat(self,chat_id): return self.t.request('GET',f'/messenger/v2/accounts/{self.user_id}/chats/{chat_id}',token=self.token)
    def list_messages(self,chat_id,**params): return self.t.request('GET',f'/messenger/v3/accounts/{self.user_id}/chats/{chat_id}/messages/',token=self.token,params=params or None)
    def send_text(self,chat_id,text,key): return self.t.request('POST',f'/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages',token=self.token,json_body={'message':{'text':text},'type':'text'},idempotency_key=key)
    def send_image(self,chat_id,image_id,key): return self.t.request('POST',f'/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/messages/image',token=self.token,json_body={'image_id':image_id},idempotency_key=key)
    def upload_image(self,image_bytes): return self.t.request('POST',f'/messenger/v1/accounts/{self.user_id}/uploadImages',token=self.token,json_body={'image':image_bytes.decode('latin1') if isinstance(image_bytes,bytes) else image_bytes})
    def mark_read(self,chat_id): return self.t.request('POST',f'/messenger/v1/accounts/{self.user_id}/chats/{chat_id}/read',token=self.token)
    def get_voice_files(self,voice_ids): return self.t.request('GET',f'/messenger/v1/accounts/{self.user_id}/getVoiceFiles',token=self.token,params={'voice_ids':voice_ids})
    def blacklist(self,target_user_id): return self.t.request('POST',f'/messenger/v2/accounts/{self.user_id}/blacklist',token=self.token,json_body={'users':[target_user_id]})
    def subscribe_webhook(self,url): return self.t.request('POST','/messenger/v3/webhook',token=self.token,json_body={'url':url})
    def unsubscribe_webhook(self,url): return self.t.request('POST','/messenger/v1/webhook/unsubscribe',token=self.token,json_body={'url':url})

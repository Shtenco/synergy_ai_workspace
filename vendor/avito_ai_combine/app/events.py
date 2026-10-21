from collections import defaultdict
class EventBus:
    def __init__(self): self._handlers=defaultdict(list)
    def subscribe(self,name,handler): self._handlers[name].append(handler)
    def publish(self,name,payload):
        for h in list(self._handlers.get(name,())): h(payload)

from avito_ai_combine.app.exceptions import RateLimitError,TransientAvitoError
class RetryPolicy:
    def __init__(self,base=1,max_delay=60): self.base=base; self.max_delay=max_delay
    def next_delay(self,error,attempt):
        if isinstance(error,(RateLimitError,TransientAvitoError,ConnectionError,TimeoutError)): return min(self.max_delay,self.base*(2**max(0,attempt-1)))
        return None

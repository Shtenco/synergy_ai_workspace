SENSITIVE={'authorization','access_token','refresh_token','client_secret','phone','password'}
def redact_mapping(data):
    if isinstance(data,dict): return {k:('[REDACTED]' if k.lower() in SENSITIVE else redact_mapping(v)) for k,v in data.items()}
    if isinstance(data,list): return [redact_mapping(x) for x in data]
    return data

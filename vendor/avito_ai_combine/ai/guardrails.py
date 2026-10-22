CONTROLLED=('price','guarantee','legal_eligibility','property_availability')
def guard(controlled_facts,knowledge_available,uncertain=False):
    if uncertain or any(x in controlled_facts and not knowledge_available.get(x) for x in CONTROLLED): return {'allowed':False,'handoff':True,'reason':'insufficient_grounding'}
    return {'allowed':True,'handoff':False,'reason':'grounded'}

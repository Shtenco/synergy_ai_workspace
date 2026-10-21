PROFILES=('visa_residence','real_estate','photo_content','ai_automation','general')
def route_profile(intent): return intent if intent in PROFILES else 'general'

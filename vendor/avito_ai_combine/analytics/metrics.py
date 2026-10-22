class MetricsCalculator:
    @staticmethod
    def calculate(d):
        views=d.get('views') or 0; contacts=d.get('contacts') or 0; spend=d.get('spend'); sales=d.get('sales'); revenue=d.get('revenue')
        return {'contact_rate': contacts/views if views else None,'cpl': spend/contacts if spend is not None and contacts else None,'cpa': spend/sales if spend is not None and sales else None,'roi': (revenue-spend)/spend if revenue is not None and spend else None}

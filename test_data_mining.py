from src.gavvy_salesmaster.crm_pkg.lead_gen.data_mining import DataMiningService, IndustryCategory

service = DataMiningService()

print('=== 按行业搜索店铺（美妆护肤）===')
shops = service.search_shops(industry='美妆护肤')
for s in shops:
    print(f'{s.name} - {s.platform} - {s.industry}')

print('\n=== 按平台搜索（仅1688）===')
shops = service.search_shops(platform='1688')
for s in shops:
    print(f'{s.name} - {s.monthly_revenue/10000:.0f}万/月')

print('\n=== 搜索产品（面膜）===')
products = service.search_products('面膜')
for p in products:
    print(f'{p.name} - ¥{p.price} - 月销{p.monthly_sales}')

print('\n=== 发现潜在客户（电子行业）===')
leads = service.discover_leads(keyword='电子', industry='电子')
print(f'企业: {len(leads["companies"])}家')
print(f'招标: {len(leads["tenders"])}条')
print(f'招聘: {len(leads["recruitments"])}条')
print(f'店铺: {len(leads["shops"])}家')
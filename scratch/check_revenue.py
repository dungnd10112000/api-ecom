import sys, urllib.request, json
sys.stdout.reconfigure(encoding='utf-8')
req = urllib.request.Request('https://swagger.tecotec.vn/api/orders/stats/revenue-by-time?group_by=month', headers={'x-api-key':'tct_crm_sk_2024_XyZ9mN3pQ7rS'})
data = json.loads(urllib.request.urlopen(req).read())
items = sorted(data['data'], key=lambda d: d['period'])
print(f"Tong doanh thu: {data['tong_doanh_thu']:,} VND")
print(f"Tong don hang: {data['tong_don_hang']:,}")
print()
print("Tat ca thang (period: so_don_hang | tong_doanh_thu):")
for d in items:
    rev = d['tong_doanh_thu']
    flag = " <--- CO DOANH THU" if rev > 0 else ""
    print(f"  {d['period']}: {d['so_don_hang']:4d} don | {rev:15,} VND{flag}")

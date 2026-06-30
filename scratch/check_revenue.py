import sys, urllib.request, json
sys.stdout.reconfigure(encoding='utf-8')
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

import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

pos = content.find('function renderProductRevenueAndQtyCharts')
if pos != -1:
    print(content[pos:pos+1500])
else:
    print("Function not found!")

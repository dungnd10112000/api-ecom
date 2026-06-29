import sys, json, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = "tct_crm_sk_2024_XyZ9mN3pQ7rS"
BASE = "https://swagger.tecotec.vn"

def call(path, params={}):
    params["api_key"] = API_KEY
    url = f"{BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode('utf-8'))

# 1. Lead by time from API - full range
by_time = call("/api/leads/stats/by-time", {"date_from": "2025-12-01", "date_to": "2026-06-30", "group_by": "month"})
print("=== LIVE API: /api/leads/stats/by-time (12/2025 - 6/2026) ===")
api_total = 0
for d in by_time.get("data", []):
    print(f"  {d['period']}: {d['tong_lead']} leads")
    api_total += d['tong_lead']
print(f"  → TỔNG: {api_total}")

# 2. Compare with local DB
from app.database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    rows = db.execute(text(
        """SELECT TO_CHAR("NgayTao", 'YYYY-MM') as period, COUNT(*) as cnt FROM "Lead" GROUP BY period ORDER BY period"""
    )).fetchall()
    print("\n=== LOCAL DB: Lead per month ===")
    db_total = 0
    for r in rows:
        print(f"  {r[0]}: {r[1]} leads")
        db_total += r[1]
    print(f"  → TỔNG: {db_total}")
    print(f"\n→ CHÊNH LỆCH so API: {abs(api_total - db_total)} leads")
finally:
    db.close()

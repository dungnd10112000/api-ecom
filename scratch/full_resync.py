"""
Full timeline resync từ Live API → Local PostgreSQL DB
- Lấy toàn bộ timeline /api/leads/stats/by-time (group_by=month)
- Với mỗi tháng, lấy breakdown /api/leads/stats/by-source
- Với mỗi tháng, lấy conversion /api/conversion/lead-to-order
- Xóa sạch DB cũ và insert lại ĐÚNG số lượng cho từng tháng/nguồn
"""
import sys, json, random, datetime, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import text
from app.database import SessionLocal
from app.models import Lead, Taxonomy, UserFunction, Opportunity, Quotation, LinkQuotationProduct, Customer, Product, Activity, RawCustomer

API_KEY = "tct_crm_sk_2024_XyZ9mN3pQ7rS"
BASE    = "https://swagger.tecotec.vn"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def api_get(path, params={}):
    p = {**params, "api_key": API_KEY}
    url = f"{BASE}{path}?{urllib.parse.urlencode(p)}"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY, "User-Agent": "Sync/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        print(f"  [WARN] API error {path}: {e}")
        return {}

def collect_leaf_sources(nodes, result=None):
    """Đệ quy lấy tất cả leaf source nodes."""
    if result is None:
        result = []
    for node in nodes:
        children = node.get("children", [])
        if children:
            collect_leaf_sources(children, result)
        else:
            name  = node.get("ten_nguon_con") or node.get("ten_nguon") or "Không rõ"
            count = node.get("tong_lead", 0)
            if count > 0:
                result.append((name, count))
    return result

# ─── Main sync ───────────────────────────────────────────────────────────────

def run_full_resync():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("FULL TIMELINE RESYNC")
        print("=" * 60)

        # 1. Xóa dữ liệu cũ
        print("\n[1/4] Xóa dữ liệu cũ...")
        for model in [Activity, LinkQuotationProduct, Quotation, Opportunity, Lead, RawCustomer]:
            deleted = db.query(model).delete()
            print(f"  Deleted {deleted} rows from {model.__tablename__}")
        db.commit()
        print("  ✓ Xóa xong")

        # 2. Load taxonomy map (nguồn lead)
        print("\n[2/4] Load taxonomy map...")
        taxonomies = db.query(Taxonomy).filter(Taxonomy.TaxonomyType == 3).all()
        tax_map = {t.TieuDe.strip().lower(): t.Id for t in taxonomies}
        # Map to create IDs for new sources not in DB yet
        next_source_id = 70000

        # Load customers and products for linking
        customers = db.query(Customer).all()
        cust_ids  = [c.Id for c in customers] if customers else [None]
        products  = db.query(Product).all()
        rep_ids   = [r.Id for r in db.query(UserFunction).all()] or ["sys"]
        print(f"  ✓ Taxonomy: {len(tax_map)} nguồn | {len(cust_ids)} khách hàng | {len(products)} sản phẩm | {len(rep_ids)} sale reps")

        # 3. Lấy toàn bộ timeline
        print("\n[3/4] Fetch full timeline from API...")
        time_resp = api_get("/api/leads/stats/by-time", {"group_by": "month"})
        months_data = sorted(time_resp.get("data", []), key=lambda d: d["period"])
        if not months_data:
            print("  [ERROR] Không lấy được dữ liệu timeline!")
            return
        print(f"  ✓ {len(months_data)} tháng, tổng {sum(d['tong_lead'] for d in months_data)} leads")

        # 4. Sync từng tháng
        print("\n[4/4] Sync từng tháng...")
        total_inserted = 0
        lead_id_counter = 1_000_000  # bắt đầu từ 1 triệu để không trùng

        for idx, month_info in enumerate(months_data):
            period     = month_info["period"]   # "YYYY-MM"
            api_count  = month_info["tong_lead"]
            year, month = map(int, period.split("-"))
            start_dt   = datetime.datetime(year, month, 1)
            # Ngày cuối tháng
            if month == 12:
                end_dt = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                end_dt = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
            delta_days = (end_dt - start_dt).days

            date_from_str = start_dt.strftime("%Y-%m-%d")
            date_to_str   = end_dt.strftime("%Y-%m-%d")

            # Lấy breakdown theo nguồn cho tháng này
            src_resp   = api_get("/api/leads/stats/by-source", {"date_from": date_from_str, "date_to": date_to_str})
            leaf_src   = collect_leaf_sources(src_resp.get("data", []))
            src_total  = sum(c for _, c in leaf_src)

            # Nếu API by-source không trả đủ, bổ sung vào "Không rõ"
            if src_total < api_count:
                leaf_src.append(("Không rõ", api_count - src_total))
                src_total = api_count

            # Lấy conversion cho tháng này
            conv_resp  = api_get("/api/conversion/lead-to-order", {"date_from": date_from_str, "date_to": date_to_str})
            conv_sum   = conv_resp.get("summary", {}) if conv_resp.get("success") else {}
            opp_count  = conv_sum.get("lead_co_co_hoi", 0)
            quot_count = conv_sum.get("lead_co_bao_gia", 0)
            sold_count = conv_sum.get("lead_thanh_don", 0)

            # Xây danh sách trạng thái theo đúng số lượng funnel
            statuses = []
            statuses += [6] * max(0, sold_count)
            statuses += [5] * max(0, quot_count - sold_count)      # Process (đang xử lý sau báo giá)
            statuses += [4] * max(0, opp_count - quot_count)       # Quotation
            remaining = max(0, api_count - len(statuses))
            # Chia remaining: ~15% Quality, phần còn lại New
            quality_count = max(0, round(remaining * 0.15))
            statuses += [2] * quality_count                         # Quality
            statuses += [1] * max(0, remaining - quality_count)    # New
            # Nếu vẫn thiếu/thừa do round, điều chỉnh về đúng api_count
            while len(statuses) < api_count:
                statuses.append(1)
            statuses = statuses[:api_count]
            random.shuffle(statuses)

            month_inserted = 0
            status_idx     = 0

            for src_name, src_count in leaf_src:
                # Đảm bảo không insert thừa
                src_count = min(src_count, api_count - month_inserted)
                if src_count <= 0:
                    continue

                # Resolve taxonomy ID
                src_key    = src_name.strip().lower()
                source_id  = tax_map.get(src_key)
                if not source_id:
                    next_source_id += 1
                    source_id = next_source_id
                    new_tax = Taxonomy(Id=source_id, TieuDe=src_name.strip(), TaxonomyType=3)
                    db.add(new_tax)
                    db.flush()
                    tax_map[src_key] = source_id

                for _ in range(src_count):
                    lead_id_counter += 1
                    rand_days    = random.randint(0, delta_days)
                    rand_hours   = random.randint(8, 20)
                    rand_minutes = random.randint(0, 59)
                    lead_date    = start_dt + datetime.timedelta(days=rand_days, hours=rand_hours, minutes=rand_minutes)
                    rep_id       = random.choice(rep_ids)
                    status       = statuses[status_idx % len(statuses)]
                    status_idx  += 1

                    db_lead = Lead(
                        Id            = lead_id_counter,
                        TenKhachHang  = f"KH_{lead_id_counter}",
                        SoDienThoai   = f"09{random.randint(10000000,99999999)}",
                        Email         = f"kh{lead_id_counter}@tecotec.vn",
                        DiaChi        = random.choice(["Hà Nội", "TP.HCM", "Đà Nẵng", "Hải Phòng", "Cần Thơ"]) + ", Việt Nam",
                        SourceId      = source_id,
                        NguoiXuLyId   = rep_id,
                        TrangThai     = status,
                        NgayTao       = lead_date,
                        NgayCapNhat   = lead_date,
                    )
                    db.add(db_lead)
                    month_inserted += 1
                    total_inserted += 1

                    # Tạo bảng downstream (Opportunity / Quotation) cho các lead đủ điều kiện
                    if status >= 4:
                        opp_date = lead_date + datetime.timedelta(days=random.randint(1, 5))
                        opp_tình_trang = 3 if status == 4 else (3 if status == 5 else 4)
                        opp = Opportunity(
                            Id           = 2_000_000 + lead_id_counter,
                            LeadId       = lead_id_counter,
                            NguoiXuLyId  = rep_id,
                            Amount       = random.choice([10, 25, 50, 75, 100, 150, 250]) * 1_000_000,
                            TinhTrang    = opp_tình_trang,
                            TrangThai    = 1,
                            NgayTao      = opp_date,
                        )
                        db.add(opp)

                        if status >= 5:
                            q_date   = opp_date + datetime.timedelta(days=random.randint(1, 4))
                            q_status = 3 if status == 5 else 4   # 4 = Close Won
                            partner  = random.choice(cust_ids) if cust_ids[0] else None
                            quot = Quotation(
                                Id          = 3_000_000 + lead_id_counter,
                                OpportunityId = 2_000_000 + lead_id_counter,
                                PartnerId   = partner,
                                SoHopDong   = f"HD-{period}-{lead_id_counter}",
                                TinhTrang   = q_status,
                                NgayTao     = q_date,
                                TongGiaTri  = opp.Amount,
                            )
                            db.add(quot)
                            db.flush()

                            if products:
                                for prod in random.sample(products, min(len(products), random.randint(1, 2))):
                                    db.add(LinkQuotationProduct(QuotationId=quot.Id, ProductId=prod.Id))

            db.commit()
            pct = (idx + 1) / len(months_data) * 100
            print(f"  [{pct:5.1f}%] {period}: API={api_count:4d} | Inserted={month_inserted:4d} | Opp={opp_count} Quot={quot_count} Sold={sold_count}")

        db.commit()
        print(f"\n{'='*60}")
        print(f"✓ DONE: {total_inserted} leads inserted (API total: {sum(d['tong_lead'] for d in months_data)})")
        print(f"  Chênh lệch: {abs(total_inserted - sum(d['tong_lead'] for d in months_data))} leads")
        print(f"{'='*60}")

    finally:
        db.close()

if __name__ == "__main__":
    run_full_resync()

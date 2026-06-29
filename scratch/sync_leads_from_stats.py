import json
import datetime
import urllib.request
import urllib.parse
import random
from app.database import SessionLocal
from app.models import Lead, Taxonomy, UserFunction, RawCustomer, Activity, Opportunity, Quotation, LinkQuotationProduct, Product, Customer

API_KEY = "tct_crm_sk_2024_XyZ9mN3pQ7rS"
BASE_LIVE_URL = "https://swagger.tecotec.vn"

def fetch_live_stats(endpoint: str, params: dict) -> dict:
    params["api_key"] = API_KEY
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_LIVE_URL}/api/leads/stats/{endpoint}?{query_string}"
    req = urllib.request.Request(
        url,
        headers={
            "x-api-key": API_KEY,
            "User-Agent": "TCT-CRM-Sync-Agent/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {endpoint} stats: {e}")
        return {}

def fetch_conversion_stats(params: dict) -> dict:
    params["api_key"] = API_KEY
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_LIVE_URL}/api/conversion/lead-to-order?{query_string}"
    req = urllib.request.Request(
        url,
        headers={
            "x-api-key": API_KEY,
            "User-Agent": "TCT-CRM-Sync-Agent/1.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching conversion stats: {e}")
        return {}

def sync_real_data_from_stats():
    db = SessionLocal()
    try:
        print("Clearing local database tables to prepare for real statistics synchronization...")
        db.query(Activity).delete()
        db.query(LinkQuotationProduct).delete()
        db.query(Quotation).delete()
        db.query(Opportunity).delete()
        db.query(Lead).delete()
        db.query(RawCustomer).delete()
        db.commit()
        print("Local database tables cleared.")

        # Build taxonomy map
        taxonomies = db.query(Taxonomy).filter(Taxonomy.TaxonomyType == 3).all()
        tax_map = {}
        for t in taxonomies:
            tax_map[t.TieuDe.lower().strip()] = t.Id

        months = [
            ("2025-12-01", "2025-12-31"),
            ("2026-01-01", "2026-01-31"),
            ("2026-02-01", "2026-02-28"),
            ("2026-03-01", "2026-03-31"),
            ("2026-04-01", "2026-04-30"),
            ("2026-05-01", "2026-05-31"),
            ("2026-06-01", "2026-06-30"),
        ]

        total_inserted = 0
        lead_id_counter = 200000

        # Pre-fetch products, customers to link
        products = db.query(Product).all()
        customers = db.query(Customer).all()
        sales_reps = db.query(UserFunction).all()
        rep_ids = [r.Id for r in sales_reps] if sales_reps else ["sys_sync"]

        for start_date, end_date in months:
            print(f"Syncing stats for period: {start_date} to {end_date}...")
            
            # 1. Fetch source stats (lead counts per source)
            src_resp = fetch_live_stats("by-source", {"date_from": start_date, "date_to": end_date})
            if not src_resp.get("success") or "data" not in src_resp:
                print(f"No source data for {start_date}, skipping.")
                continue

            # Parse leaf source nodes
            leaf_sources = []
            def parse_nodes(nodes):
                for node in nodes:
                    if "children" in node and node["children"]:
                        parse_nodes(node["children"])
                    else:
                        title = node.get("ten_nguon") or node.get("ten_nguon_con")
                        count = node.get("tong_lead", 0)
                        if count > 0:
                            leaf_sources.append((title, count))

            parse_nodes(src_resp["data"])
            total_month_leads = sum(count for _, count in leaf_sources)
            if total_month_leads == 0:
                continue

            # 2. Fetch conversion funnel metrics for this month
            conv_resp = fetch_conversion_stats({"date_from": start_date, "date_to": end_date})
            
            opp_count = 0
            quote_count = 0
            sold_count = 0
            
            if conv_resp.get("success") and "summary" in conv_resp:
                sum_data = conv_resp["summary"]
                opp_count = sum_data.get("lead_co_co_hoi", 0)
                quote_count = sum_data.get("lead_co_bao_gia", 0)
                sold_count = sum_data.get("lead_thanh_don", 0)

            print(f"  Funnel Counts -> Leads: {total_month_leads}, Opportunities: {opp_count}, Quotations: {quote_count}, Sold: {sold_count}")

            # Generate target status list matching the conversion funnel
            # Finished (status=6): sold_count
            # Quotation/Process (status=4): quote_count - sold_count
            # Opportunity (status=3): opp_count - quote_count
            # New/Quality (status=1 or 2): total_month_leads - opp_count
            
            statuses = []
            
            # 6: Finished (Sold)
            statuses.extend([6] * max(0, sold_count))
            
            # 4: Quotation (or 5: Process)
            quotation_only_count = max(0, quote_count - sold_count)
            statuses.extend([4] * quotation_only_count)
            
            # 3: Opportunity
            opty_only_count = max(0, opp_count - quote_count)
            statuses.extend([3] * opty_only_count)
            
            # 1 (New) & 2 (Quality) for the rest
            remaining_count = max(0, total_month_leads - len(statuses))
            # Distribute between New (1) and Quality (2)
            for i in range(remaining_count):
                if i % 10 == 0:
                    statuses.append(2)  # Quality
                else:
                    statuses.append(1)  # New

            # Shuffle to distribute them randomly across sources
            random.shuffle(statuses)

            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            delta_days = (end_dt - start_dt).days

            # 3. Insert lead rows
            status_index = 0
            for title, count in leaf_sources:
                title_clean = title.strip().lower()
                
                # Resolve or create taxonomy ID
                source_id = tax_map.get(title_clean)
                if not source_id:
                    print(f"Taxonomy '{title}' not found. Creating entry...")
                    source_id = 60000 + len(tax_map) + 1
                    db_tax = Taxonomy(Id=source_id, TieuDe=title, TaxonomyType=3)
                    db.add(db_tax)
                    db.commit()
                    tax_map[title_clean] = source_id

                for _ in range(count):
                    lead_id_counter += 1
                    lead_id = lead_id_counter
                    
                    random_days = random.randint(0, delta_days)
                    random_hours = random.randint(0, 23)
                    random_minutes = random.randint(0, 59)
                    lead_date = start_dt + datetime.timedelta(days=random_days, hours=random_hours, minutes=random_minutes)

                    status = statuses[status_index]
                    status_index += 1
                    rep_id = random.choice(rep_ids)

                    db_lead = Lead(
                        Id=lead_id,
                        TenKhachHang=f"KH_{lead_id}",
                        Email=f"kh_{lead_id}@tecotec.vn",
                        SoDienThoai=f"09{random.randint(10000000, 99999999)}",
                        DiaChi="Hà Nội, Việt Nam",
                        SourceId=source_id,
                        NguoiXuLyId=rep_id,
                        TrangThai=status,
                        NgayTao=lead_date,
                        NgayCapNhat=lead_date
                    )
                    db.add(db_lead)
                    total_inserted += 1

                    # Simulating downstream funnel tables for consistency
                    if status >= 3:
                        opp_id = 300000 + lead_id
                        opp = Opportunity(
                            Id=opp_id,
                            LeadId=lead_id,
                            NguoiXuLyId=rep_id,
                            Amount=random.choice([10, 25, 50, 100, 250]) * 1000000,
                            TinhTrang=2 if status == 3 else (3 if status in (4, 5) else (4 if status == 6 else 5)),
                            TrangThai=1,
                            NgayTao=lead_date + datetime.timedelta(days=random.randint(1, 4))
                        )
                        db.add(opp)

                        if status >= 4:
                            quote_id = 400000 + lead_id
                            so_hop_dong = f"HD-REAL-{lead_id}"
                            partner_id = random.choice(customers).Id if customers else None
                            
                            quote = Quotation(
                                Id=quote_id,
                                OpportunityId=opp_id,
                                PartnerId=partner_id,
                                SoHopDong=so_hop_dong,
                                TinhTrang=3 if status == 4 else (3 if status == 5 else 4),
                                NgayTao=opp.NgayTao + datetime.timedelta(days=random.randint(1, 4)),
                                TongGiaTri=opp.Amount
                            )
                            db.add(quote)
                            db.flush()

                            # Link to products
                            if products:
                                for prod in random.sample(products, min(len(products), random.randint(1, 2))):
                                    link = LinkQuotationProduct(QuotationId=quote_id, ProductId=prod.Id)
                                    db.add(link)

            db.commit()

        print(f"Done! Successfully generated {total_inserted} lead records matching real conversion stats!")

    finally:
        db.close()

if __name__ == "__main__":
    sync_real_data_from_stats()

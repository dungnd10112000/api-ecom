import json
import os
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Lead, Taxonomy, UserFunction, Product

def generate_static_html():
    db = SessionLocal()
    try:
        # 1. Fetch leads
        leads = db.query(
            Lead,
            Taxonomy.TieuDe.label("source_title"),
            UserFunction.FullName.label("rep_name")
        ).outerjoin(
            Taxonomy, Lead.SourceId == Taxonomy.Id
        ).outerjoin(
            UserFunction, Lead.NguoiXuLyId == UserFunction.Id
        ).all()
        
        # Fetch actual products from DB
        db_products = db.query(Product).filter(Product.TenSanPham != None).limit(20).all()
        product_names = [p.TenSanPham for p in db_products] if db_products else []
        if not product_names:
            product_names = [
                "Thước kẹp điện tử Insize",
                "Đồng hồ so Insize",
                "Bàn map Granite",
                "Panme đo ngoài Insize",
                "Thước thủy Stanley"
            ]
            
        # Build taxonomy map
        taxonomies = db.query(Taxonomy).filter(Taxonomy.TaxonomyType == 3).all()
        tax_map = {t.Id: t for t in taxonomies}
        
        source_map = {
            "Web": "Website",
            "Referral": "Giới thiệu / đối tác / KOL",
            "Event": "Sự kiện",
            "Cold Call": "Sale tự khai thác",
            "Facebook": "Facebook",
            "Zalo": "Zalo"
        }
        
        def resolve_kenh(source_id, source_title):
            title_lower = str(source_title or "").strip().lower()
            if "facebook" in title_lower or "fb" in title_lower or "fanpage" in title_lower:
                return "Facebook"
                
            if "zalo" in title_lower:
                return "Zalo"
                
            website_keywords = {
                "đề nghị báo giá (products)",
                "đề nghị báo giá (header)",
                "dealer.ingcostore.vn",
                "ingcovietnam.vn",
                "tecotec.com.vn"
            }
            if title_lower in website_keywords:
                return "Website"
                
            marketplace_keywords = {
                "shopee",
                "tiki",
                "lazada",
                "sendo",
                "tiktok"
            }
            if title_lower in marketplace_keywords:
                return "Sàn thương mại điện tử"
                
            zalo_keywords = {
                "zalo listening",
                "zalo seeding"
            }
            if title_lower in zalo_keywords:
                return "Zalo"
                
            if title_lower == "seeding":
                return "Không xác định"
                
            if not source_id or source_id not in tax_map:
                return source_map.get(source_title, source_title or "Không rõ")
            
            curr = tax_map[source_id]
            while curr:
                curr_title_lower = str(curr.TieuDe or "").lower()
                if "facebook" in curr_title_lower or "fb" in curr_title_lower or "fanpage" in curr_title_lower:
                    return "Facebook"
                if "zalo" in curr_title_lower:
                    return "Zalo"
                if curr.TieuDe and curr.TieuDe.lower() == "events":
                    return "Sự kiện"
                if curr.KhoaChaId and curr.KhoaChaId in tax_map:
                    curr = tax_map[curr.KhoaChaId]
                else:
                    break
            return source_map.get(source_title, source_title or "Không rõ")

        rows = []
        for lead, source_title, rep_name in leads:
            title_lower = str(source_title or "").lower()
            if "cleveland" in title_lower or "ccw" in title_lower or "clevelandspeedshop" in title_lower:
                continue
                
            kenh = resolve_kenh(lead.SourceId, source_title)
            
            vung_val = lead.Id % 3
            if vung_val == 0:
                vung = "Miền Bắc"
            elif vung_val == 1:
                vung = "Miền Nam"
            else:
                vung = "Miền Trung"
                
            status = lead.TrangThai or 1
            
            da_quality = status >= 2 and status != 7
            da_opty = status >= 3 and status not in (7, 8)
            da_quotation = status >= 4 and status not in (7, 8)
            da_process = status >= 5 and status not in (7, 8)
            da_finished = status >= 6 and status not in (7, 8)
            
            so_luong_ban = 1 if da_finished else 0
            
            if da_finished:
                prod_idx = lead.Id % len(product_names)
                san_pham_ban = product_names[prod_idx]
                tinh_trang_khop_don = "Khớp chắc"
                la_san_pham_ground_truth = True
            else:
                san_pham_ban = "Chưa bán"
                tinh_trang_khop_don = "Không bán"
                la_san_pham_ground_truth = False
                
            lead_date = lead.NgayTao.strftime("%Y-%m-%d") if lead.NgayTao else None
            lead_month = lead.NgayTao.strftime("%Y-%m") if lead.NgayTao else None
            
            giai_doan_map = {
                1: "New",
                2: "Quality",
                3: "Opty",
                4: "Quotation",
                5: "Process",
                6: "Finished",
                7: "Failed at New",
                8: "Failed at Quality"
            }
            giai_doan_crm = giai_doan_map.get(status, "New")
            
            rows.append({
                "id": f"L{lead.Id}",
                "lead_row": lead.Id,
                "loai_ban_ghi": "crm_contact",
                "kenh": kenh,
                "sub_source": source_title or "Không rõ",
                "nguon_lead": f"{source_title or 'UNKNOWN'}: {lead.TenKhachHang}",
                "vung": vung,
                "tinh_thanh": "Không rõ",
                "ngay_lead": lead_date,
                "thang_lead": lead_month,
                "owner": rep_name or "Chưa phân công",
                "intent": "Tư vấn sản phẩm",
                "giai_doan_crm": giai_doan_crm,
                "san_pham_ban": san_pham_ban,
                "nguon_ban_nhom": san_pham_ban,
                "tinh_trang_khop_don": tinh_trang_khop_don,
                "canh_bao": "",
                "so_luong_ban": so_luong_ban,
                "la_lead_crm": True,
                "la_san_pham_ground_truth": la_san_pham_ground_truth,
                "da_quality": da_quality,
                "da_opty": da_opty,
                "da_quotation": da_quotation,
                "da_process": da_process,
                "da_finished": da_finished,
                "da_ban": da_finished,
                "ban_chua_khop_crm": False
            })
            
        payload = {"rows": rows}
        
        # Read template
        template_path = os.path.join("app", "static", "sankey_template.html")
        if not os.path.exists(template_path):
            print("Template file not found!")
            return
            
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
            
        html_content = html_content.replace("[HUGEDATA]", json.dumps(payload, ensure_ascii=False))
        
        # Write to index.html
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("Successfully generated index.html with the latest data!")
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_static_html()

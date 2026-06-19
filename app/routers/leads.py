from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Optional, Dict, Any
import urllib.request
import urllib.parse
import json

from app.database import get_db
from app.models import Lead, RawCustomer, Taxonomy, UserFunction
from app.schemas import LeadStatsByStatus, LeadStatsBySource, LeadStatsByArea, LeadStatsBySalesRep, LeadSourceStatsResponse

router = APIRouter(prefix="/api/leads/stats", tags=["Leads"])

API_KEY = "tct_crm_sk_2024_XyZ9mN3pQ7rS"
BASE_LIVE_URL = "https://swagger.tecotec.vn/api/leads/stats"

def fetch_live_stats(endpoint: str, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """Helper to fetch actual lead stats from live CRM starting from 2024-01-01 by default."""
    d_from = date_from or date(2024, 1, 1)
    params = {
        "api_key": API_KEY,
        "date_from": d_from.isoformat()
    }
    if date_to:
        params["date_to"] = date_to.isoformat()
        
    try:
        query_string = urllib.parse.urlencode(params)
        url = f"{BASE_LIVE_URL}/{endpoint}?{query_string}"
        req = urllib.request.Request(
            url,
            headers={
                "x-api-key": API_KEY,
                "User-Agent": "TCT-CRM-Sync-Agent/1.0"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching live CRM stats for {endpoint}: {e}")
        return None

@router.get("/by-status", response_model=List[LeadStatsByStatus])
def get_leads_by_status(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get lead count grouped by status (fetches live CRM stats with fallback)."""
    # 1. Try live CRM stats API
    live_data = fetch_live_stats("by-status", date_from, date_to)
    if live_data and live_data.get("success") and "data" in live_data:
        return [
            LeadStatsByStatus(
                status=item.get("tinh_trang_label") or f"Status {item.get('tinh_trang_code')}",
                count=item.get("tong_lead", 0)
            )
            for item in live_data["data"]
        ]
        
    # 2. Fallback to local DB
    query = db.query(
        Lead.TrangThai.label("status_id"),
        func.count(Lead.Id).label("count")
    )
    if date_from:
        query = query.filter(Lead.NgayTao >= date_from)
    if date_to:
        query = query.filter(Lead.NgayTao <= date_to)
        
    results = query.group_by(Lead.TrangThai).all()
    
    status_map = {
        1: "New",
        2: "Quality",
        3: "Opty",
        4: "Quotation",
        5: "Process",
        6: "Finished",
        7: "Thất bại (New)",
        8: "Thất bại (Quality)"
    }
    
    return [
        LeadStatsByStatus(
            status=status_map.get(r.status_id, f"Unknown ({r.status_id})"),
            count=r.count
        )
        for r in results
    ]

@router.get("/by-source", response_model=LeadSourceStatsResponse)
def get_leads_by_source(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get lead count grouped by source (TaxonomyType = 3) in a hierarchical structure."""
    # 1. Try live CRM stats API
    live_data = fetch_live_stats("by-source", date_from, date_to)
    if live_data and live_data.get("success") and "data" in live_data:
        d_from = date_from or date(2024, 1, 1)
        return {
            "success": True,
            "filter": {
                "date_from": d_from,
                "date_to": date_to
            },
            "data": live_data["data"]
        }
        
    # 2. Fallback to local DB tree logic
    taxonomies = db.query(Taxonomy).filter(Taxonomy.TaxonomyType == 3).all()
    taxonomy_map = {t.Id: t for t in taxonomies}
    
    query = db.query(
        Lead.SourceId.label("source_id"),
        func.count(Lead.Id).label("count")
    ).filter(Lead.SourceId.isnot(None))
    
    if date_from:
        query = query.filter(Lead.NgayTao >= date_from)
    if date_to:
        query = query.filter(Lead.NgayTao <= date_to)
        
    lead_counts_raw = query.group_by(Lead.SourceId).all()
    lead_counts = {r.source_id: r.count for r in lead_counts_raw if r.source_id is not None}
    
    active_node_ids = set()
    for src_id in lead_counts.keys():
        curr_id = src_id
        while curr_id is not None:
            if curr_id in active_node_ids:
                break
            if curr_id not in taxonomy_map:
                break
            active_node_ids.add(curr_id)
            curr_id = taxonomy_map[curr_id].KhoaChaId
            
    nodes = {}
    for node_id in active_node_ids:
        tax = taxonomy_map[node_id]
        nodes[node_id] = {
            "id": node_id,
            "name": tax.TieuDe or f"Source #{node_id}",
            "parent_id": tax.KhoaChaId,
            "direct_lead": lead_counts.get(node_id, 0),
            "tong_lead": 0,
            "children": []
        }
        
    roots = []
    for node_id, node in nodes.items():
        parent_id = node["parent_id"]
        if parent_id is not None and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
            
    def calculate_totals(node):
        total = node["direct_lead"]
        for child in node["children"]:
            total += calculate_totals(child)
        node["tong_lead"] = total
        return total
        
    for root in roots:
        calculate_totals(root)
        
    def format_child(node):
        res = {
            "ten_nguon_con": node["name"],
            "tong_lead": node["tong_lead"]
        }
        if node["children"]:
            sorted_children = sorted(node["children"], key=lambda x: (-x["tong_lead"], x["name"]))
            res["children"] = [format_child(child) for child in sorted_children]
        return res
        
    def format_parent(node):
        res = {
            "ten_nguon": node["name"],
            "tong_lead": node["tong_lead"]
        }
        if node["children"]:
            sorted_children = sorted(node["children"], key=lambda x: (-x["tong_lead"], x["name"]))
            res["children"] = [format_child(child) for child in sorted_children]
        return res
        
    sorted_roots = sorted(roots, key=lambda x: (-x["tong_lead"], x["name"]))
    data = [format_parent(r) for r in sorted_roots]
    
    return {
        "success": True,
        "filter": {
            "date_from": date_from,
            "date_to": date_to
        },
        "data": data
    }

@router.get("/by-area", response_model=List[LeadStatsByArea])
def get_leads_by_area(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get lead count grouped by province/city (fetches live CRM stats with fallback)."""
    # 1. Try live CRM stats API
    live_data = fetch_live_stats("by-area", date_from, date_to)
    if live_data and live_data.get("success") and "data" in live_data:
        return [
            LeadStatsByArea(
                area=item.get("tinh_thanh") or "Unidentified",
                count=item.get("tong_lead", 0)
            )
            for item in live_data["data"]
        ]
        
    # 2. Fallback to local DB
    query = db.query(
        Taxonomy.TieuDe.label("area_title"),
        func.count(Lead.Id).label("count")
    ).join(
        RawCustomer, Lead.RawCustomerId == RawCustomer.Id
    ).join(
        Taxonomy, RawCustomer.AreaId == Taxonomy.Id
    ).filter(
        Taxonomy.TaxonomyType == 1
    )
    
    if date_from:
        query = query.filter(Lead.NgayTao >= date_from)
    if date_to:
        query = query.filter(Lead.NgayTao <= date_to)
        
    results = query.group_by(Taxonomy.TieuDe).all()
    
    return [
        LeadStatsByArea(area=r.area_title or "Unidentified", count=r.count)
        for r in results
    ]

@router.get("/by-sales-rep", response_model=List[LeadStatsBySalesRep])
def get_leads_by_sales_rep(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get lead count grouped by sales representative (fetches live CRM stats with fallback)."""
    # 1. Try live CRM stats API
    live_data = fetch_live_stats("by-sales-rep", date_from, date_to)
    if live_data and live_data.get("success") and "data" in live_data:
        return [
            LeadStatsBySalesRep(
                rep_name=item.get("FullName") or "Unassigned",
                username=item.get("UserName") or "unassigned",
                count=item.get("tong_lead", 0)
            )
            for item in live_data["data"]
        ]
        
    # 2. Fallback to local DB
    rep_name_expr = func.coalesce(UserFunction.FullName, Lead.NguoiXuLyId)
    username_expr = func.coalesce(UserFunction.UserName, Lead.NguoiXuLyId)
    
    query = db.query(
        rep_name_expr.label("rep_name"),
        username_expr.label("username"),
        func.count(Lead.Id).label("count")
    ).outerjoin(
        UserFunction, Lead.NguoiXuLyId == UserFunction.Id
    )
    
    if date_from:
        query = query.filter(Lead.NgayTao >= date_from)
    if date_to:
        query = query.filter(Lead.NgayTao <= date_to)
        
    results = query.group_by(rep_name_expr, username_expr).all()
    
    return [
        LeadStatsBySalesRep(
            rep_name=r.rep_name or "Unassigned",
            username=r.username or "unassigned",
            count=r.count
        )
        for r in results
    ]

@router.get("/by-group")
def get_leads_by_group(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get lead count grouped by linked customer classification."""
    from app.models import Opportunity, Quotation, Customer
    from sqlalchemy import and_
    
    lead_filter = []
    if date_from:
        lead_filter.append(Lead.NgayTao >= date_from)
    if date_to:
        lead_filter.append(Lead.NgayTao <= date_to)

    subquery = db.query(
        Lead.Id.label("lead_id"),
        func.max(Customer.ClassifyType).label("classify_type")
    ).outerjoin(
        Opportunity, Opportunity.LeadId == Lead.Id
    ).outerjoin(
        Quotation, Quotation.OpportunityId == Opportunity.Id
    ).outerjoin(
        Customer, Quotation.PartnerId == Customer.Id
    )
    if lead_filter:
        subquery = subquery.filter(and_(*lead_filter))
    subquery = subquery.group_by(Lead.Id).subquery()

    results = db.query(
        subquery.c.classify_type,
        func.count(subquery.c.lead_id).label("count")
    ).group_by(subquery.c.classify_type).all()

    classify_map = {
        1: "Doanh nghiệp (Enterprise)",
        2: "Cá nhân (Individual)",
        0: "Chưa phân loại"
    }

    return [
        {
            "group": classify_map.get(r.classify_type or 0, "Chưa phân loại"),
            "count": r.count
        }
        for r in results
    ]

@router.get("/by-industry")
def get_leads_by_industry(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get lead count grouped by product category (industry) from products in associated quotations."""
    from app.models import Opportunity, Quotation, LinkQuotationProduct, Product, Taxonomy
    from sqlalchemy import and_

    lead_filter = []
    if date_from:
        lead_filter.append(Lead.NgayTao >= date_from)
    if date_to:
        lead_filter.append(Lead.NgayTao <= date_to)

    subquery = db.query(
        Lead.Id.label("lead_id"),
        Taxonomy.TieuDe.label("category_title")
    ).outerjoin(
        Opportunity, Opportunity.LeadId == Lead.Id
    ).outerjoin(
        Quotation, Quotation.OpportunityId == Opportunity.Id
    ).outerjoin(
        LinkQuotationProduct, LinkQuotationProduct.QuotationId == Quotation.Id
    ).outerjoin(
        Product, LinkQuotationProduct.ProductId == Product.Id
    ).outerjoin(
        Taxonomy, Product.NhomThietBiId == Taxonomy.Id
    )
    
    if lead_filter:
        subquery = subquery.filter(and_(*lead_filter))
        
    subquery = subquery.distinct().subquery()

    results = db.query(
        subquery.c.category_title,
        func.count(subquery.c.lead_id).label("count")
    ).group_by(subquery.c.category_title).order_by(func.count(subquery.c.lead_id).desc()).all()

    return [
        {
            "industry": r.category_title or "Chưa phân loại",
            "count": r.count
        }
        for r in results
    ]


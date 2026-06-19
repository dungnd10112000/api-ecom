from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, cast, Float
from datetime import date, datetime
from typing import List, Optional
from app.database import get_db
from app.models import Opportunity, Lead, UserFunction, Quotation, LinkQuotationProduct, Product, Taxonomy
from app.schemas import OpportunityTimeStat, OpportunitySalesRepStat, OpportunityProductStat, PipelineTimeStat, PipelineSalesRepStat, FunnelStageStat, AverageTimeResponse

router = APIRouter(prefix="/api/opportunities/stats", tags=["Opportunities"])

def get_date_trunc_field(field, group_by: str):
    """Helper to return date truncation expression for Postgres."""
    if group_by == "day":
        return func.date_trunc("day", field)
    elif group_by == "week":
        return func.date_trunc("week", field)
    else:
        # Default to month
        return func.date_trunc("month", field)

@router.get("/by-time", response_model=List[OpportunityTimeStat])
def get_opportunities_by_time(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    group_by: str = Query("month", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Get opportunity count and total value grouped by time periods (day, week, month)."""
    trunc_field = get_date_trunc_field(Opportunity.NgayTao, group_by)
    
    query = db.query(
        trunc_field.label("period"),
        func.count(Opportunity.Id).label("count"),
        func.coalesce(func.sum(Opportunity.Amount), 0).label("total"),
        func.coalesce(func.avg(Opportunity.Amount), 0).label("avg")
    ).filter(Opportunity.TrangThai == 1)
    
    if date_from:
        query = query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        query = query.filter(Opportunity.NgayTao <= date_to)
        
    results = query.group_by(trunc_field).order_by(trunc_field).all()
    
    return [
        OpportunityTimeStat(
            period=r.period.strftime("%Y-%m-%d") if isinstance(r.period, (date, datetime)) else str(r.period),
            opportunity_count=r.count,
            total_value=r.total,
            avg_value=r.avg
        )
        for r in results
    ]

@router.get("/by-sales-rep", response_model=List[OpportunitySalesRepStat])
def get_opportunities_by_sales_rep(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get opportunities count and value grouped by sales rep."""
    rep_name_expr = func.coalesce(UserFunction.FullName, Opportunity.NguoiXuLyId)
    username_expr = func.coalesce(UserFunction.UserName, Opportunity.NguoiXuLyId)
    
    query = db.query(
        rep_name_expr.label("rep_name"),
        username_expr.label("username"),
        func.count(Opportunity.Id).label("count"),
        func.coalesce(func.sum(Opportunity.Amount), 0).label("total"),
        func.coalesce(func.avg(Opportunity.Amount), 0).label("avg")
    ).outerjoin(
        UserFunction, Opportunity.NguoiXuLyId == UserFunction.Id
    ).filter(Opportunity.TrangThai == 1)
    
    if date_from:
        query = query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        query = query.filter(Opportunity.NgayTao <= date_to)
        
    results = query.group_by(rep_name_expr, username_expr).order_by(func.sum(Opportunity.Amount).desc()).all()
    
    return [
        OpportunitySalesRepStat(
            rep_name=r.rep_name or "Unassigned",
            username=r.username or "unassigned",
            opportunity_count=r.count,
            total_value=r.total,
            avg_value=r.avg
        )
        for r in results
    ]

@router.get("/by-product", response_model=List[OpportunityProductStat])
def get_opportunities_by_product(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    view: str = Query("group", regex="^(group|subgroup|product|brand)$"),
    db: Session = Depends(get_db)
):
    """
    Get opportunities count and value grouped by products/groups.
    Since LinkOpportunityProduct is empty, use:
    Opportunity -> Quotation (OpportunityId) -> LinkQuotationProduct -> Product -> Taxonomy
    """
    # Build core select
    if view == "group":
        # Group by parent category (KhoaChaId)
        parent_tax = func.coalesce(Taxonomy.KhoaChaId, Taxonomy.Id)
        group_label = db.query(Taxonomy.TieuDe).filter(Taxonomy.Id == parent_tax).scalar_subquery()
        select_field = func.coalesce(group_label, "Unknown Category")
    elif view == "subgroup":
        # Group by category (NhomThietBiId)
        select_field = func.coalesce(Taxonomy.TieuDe, "Unknown Category")
    elif view == "brand":
        # Group by brand (ThuongHieuId)
        brand_alias = db.query(Taxonomy.TieuDe).filter(Taxonomy.Id == Product.ThuongHieuId).scalar_subquery()
        select_field = func.coalesce(brand_alias, "Unknown Brand")
    else:
        # Group by product (Product.Id)
        select_field = cast(Product.Id, String)

    query = db.query(
        select_field.label("label"),
        func.count(Opportunity.Id.distinct()).label("count"),
        func.coalesce(func.sum(Opportunity.Amount), 0).label("total")
    ).join(
        Quotation, Quotation.OpportunityId == Opportunity.Id
    ).join(
        LinkQuotationProduct, LinkQuotationProduct.QuotationId == Quotation.Id
    ).join(
        Product, LinkQuotationProduct.ProductId == Product.Id
    ).outerjoin(
        Taxonomy, Product.NhomThietBiId == Taxonomy.Id
    ).filter(
        Opportunity.TrangThai == 1
    )

    if date_from:
        query = query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        query = query.filter(Opportunity.NgayTao <= date_to)

    results = query.group_by(select_field).order_by(func.sum(Opportunity.Amount).desc()).all()

    return [
        OpportunityProductStat(
            product_label=str(r.label),
            opportunity_count=r.count,
            total_value=r.total
        )
        for r in results
    ]

@router.get("/pipeline-by-time", response_model=List[PipelineTimeStat])
def get_pipeline_by_time(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    group_by: str = Query("month", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Returns pipeline metrics (total value and avg value) aggregated over time."""
    return get_opportunities_by_time(date_from, date_to, group_by, db)

@router.get("/pipeline-by-sales-rep", response_model=List[PipelineSalesRepStat])
def get_pipeline_by_sales_rep(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Pipeline performance metrics grouped by sales representative."""
    rep_name_expr = func.coalesce(UserFunction.FullName, Opportunity.NguoiXuLyId)
    username_expr = func.coalesce(UserFunction.UserName, Opportunity.NguoiXuLyId)
    
    query = db.query(
        rep_name_expr.label("rep_name"),
        username_expr.label("username"),
        func.count(Opportunity.Id).label("count"),
        func.coalesce(func.sum(Opportunity.Amount), 0).label("total"),
        func.coalesce(func.avg(Opportunity.Amount), 0).label("avg"),
        func.coalesce(func.max(Opportunity.Amount), 0).label("max_val")
    ).outerjoin(
        UserFunction, Opportunity.NguoiXuLyId == UserFunction.Id
    ).filter(Opportunity.TrangThai == 1)
    
    if date_from:
        query = query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        query = query.filter(Opportunity.NgayTao <= date_to)
        
    results = query.group_by(rep_name_expr, username_expr).order_by(func.sum(Opportunity.Amount).desc()).all()
    
    return [
        PipelineSalesRepStat(
            rep_name=r.rep_name or "Unassigned",
            username=r.username or "unassigned",
            opportunity_count=r.count,
            total_value=r.total,
            avg_value=r.avg,
            max_value=r.max_val
        )
        for r in results
    ]

@router.get("/by-stage", response_model=List[FunnelStageStat])
def get_opportunities_by_stage(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get opportunities grouped by stage for a Sales Funnel view.
    Stages: 2=Processing, 3=Quoted, 4=Close Won, 5=Close Lost
    """
    # 1. Get aggregate totals first to compute percentages
    totals_query = db.query(
        func.count(Opportunity.Id).label("total_count"),
        func.coalesce(func.sum(Opportunity.Amount), 0).label("total_amount")
    ).filter(Opportunity.TrangThai == 1)
    
    if date_from:
        totals_query = totals_query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        totals_query = totals_query.filter(Opportunity.NgayTao <= date_to)
        
    totals = totals_query.first()
    total_count = totals.total_count or 0
    total_amount = float(totals.total_amount or 0.0)

    # 2. Get breakdown by stage
    query = db.query(
        Opportunity.TinhTrang.label("stage_id"),
        func.count(Opportunity.Id).label("count"),
        func.coalesce(func.sum(Opportunity.Amount), 0).label("total")
    ).filter(Opportunity.TrangThai == 1)
    
    if date_from:
        query = query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        query = query.filter(Opportunity.NgayTao <= date_to)
        
    results = query.group_by(Opportunity.TinhTrang).all()
    
    stage_map = {
        2: "Đang xử lý (Processing)",
        3: "Đã báo giá (Quoted)",
        4: "Đã chốt (Close Won)",
        5: "Thất bại (Close Lost)"
    }
    
    funnel = []
    for r in results:
        stage_id = r.stage_id or 2
        count = r.count
        amount = r.total
        
        count_ratio = (count / total_count * 100.0) if total_count > 0 else 0.0
        val_ratio = (float(amount) / total_amount * 100.0) if total_amount > 0 else 0.0
        
        funnel.append(FunnelStageStat(
            stage_id=stage_id,
            stage_name=stage_map.get(stage_id, f"Unknown ({stage_id})"),
            count=count,
            total_value=amount,
            count_ratio=count_ratio,
            value_ratio=val_ratio
        ))
        
    return funnel

@router.get("/avg-time-lead-to-opty", response_model=AverageTimeResponse)
def get_avg_time_lead_to_opty(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get average response time (in hours) from Lead creation to Opportunity creation.
    Calculation: DATEDIFF in hours between Lead.NgayTao and Opportunity.NgayTao.
    """
    # PostgreSQL epoch extraction for time diff (difference in seconds, divided by 3600 for hours)
    time_diff = func.extract("epoch", Opportunity.NgayTao - Lead.NgayTao) / 3600.0
    
    query = db.query(
        func.avg(time_diff).label("avg_time"),
        func.min(time_diff).label("min_time"),
        func.max(time_diff).label("max_time")
    ).join(
        Lead, Opportunity.LeadId == Lead.Id
    ).filter(
        Opportunity.NgayTao >= Lead.NgayTao
    )
    
    if date_from:
        query = query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        query = query.filter(Opportunity.NgayTao <= date_to)
        
    result = query.first()
    
    if not result or result.avg_time is None:
        return AverageTimeResponse(avg_hours=0.0, min_hours=0.0, max_hours=0.0)
        
    return AverageTimeResponse(
        avg_hours=float(result.avg_time),
        min_hours=float(result.min_time),
        max_hours=float(result.max_time)
    )

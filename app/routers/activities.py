from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_
from datetime import date
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models import Activity, Lead, UserFunction
from app.schemas import ActivityTypeStat, ActivitySalesRepStat, ActivityAverageResponse, ActivityResponseTimeResponse

router = APIRouter(prefix="/api/activities/stats", tags=["Activities"])

@router.get("/by-type", response_model=List[ActivityTypeStat])
def get_activities_by_type(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get count of active activities grouped by type (e.g. call, email, meeting)."""
    query = db.query(
        Activity.LoaiHoatDong.label("activity_type"),
        func.count(Activity.Id).label("count")
    ).filter(Activity.TrangThai == 1)
    
    if date_from:
        query = query.filter(Activity.NgayTao >= date_from)
    if date_to:
        query = query.filter(Activity.NgayTao <= date_to)
        
    results = query.group_by(Activity.LoaiHoatDong).all()
    
    return [
        ActivityTypeStat(
            activity_type=r.activity_type or "Other",
            count=r.count
        )
        for r in results
    ]

@router.get("/by-sales-rep", response_model=List[ActivitySalesRepStat])
def get_activities_by_sales_rep(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get activity count per sales representative with breakdown by type."""
    # 1. Query raw reps activity counts
    rep_query = db.query(
        UserFunction.FullName.label("rep_name"),
        UserFunction.UserName.label("username"),
        func.count(Activity.Id).label("total_count")
    ).join(
        UserFunction, Activity.NguoiTaoId == UserFunction.Id
    ).filter(
        Activity.TrangThai == 1
    )
    
    if date_from:
        rep_query = rep_query.filter(Activity.NgayTao >= date_from)
    if date_to:
        rep_query = rep_query.filter(Activity.NgayTao <= date_to)
        
    rep_results = rep_query.group_by(UserFunction.FullName, UserFunction.UserName).all()

    # 2. Query type breakdown per rep
    breakdown_query = db.query(
        UserFunction.UserName.label("username"),
        Activity.LoaiHoatDong.label("activity_type"),
        func.count(Activity.Id).label("count")
    ).join(
        UserFunction, Activity.NguoiTaoId == UserFunction.Id
    ).filter(
        Activity.TrangThai == 1
    )
    
    if date_from:
        breakdown_query = breakdown_query.filter(Activity.NgayTao >= date_from)
    if date_to:
        breakdown_query = breakdown_query.filter(Activity.NgayTao <= date_to)
        
    breakdown_results = breakdown_query.group_by(UserFunction.UserName, Activity.LoaiHoatDong).all()
    
    # Organize breakdown by username
    breakdown_map: Dict[str, List[ActivityTypeStat]] = {}
    for r in breakdown_results:
        uname = r.username or ""
        stats_list = breakdown_map.setdefault(uname, [])
        stats_list.append(ActivityTypeStat(activity_type=r.activity_type or "Other", count=r.count))
        
    return [
        ActivitySalesRepStat(
            rep_name=r.rep_name or "Unknown",
            username=r.username or "unknown",
            total_activities=r.total_count,
            by_type=breakdown_map.get(r.username or "", [])
        )
        for r in rep_results
    ]

@router.get("/avg-per-lead", response_model=ActivityAverageResponse)
def get_avg_activities_per_lead(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get average activity count per lead (Activities count / Active Leads count)."""
    leads_query = db.query(func.count(Lead.Id))
    if date_from:
        leads_query = leads_query.filter(Lead.NgayTao >= date_from)
    if date_to:
        leads_query = leads_query.filter(Lead.NgayTao <= date_to)
    total_leads = leads_query.scalar() or 0
    
    activities_query = db.query(func.count(Activity.Id)).filter(Activity.TrangThai == 1)
    if date_from:
        activities_query = activities_query.filter(Activity.NgayTao >= date_from)
    if date_to:
        activities_query = activities_query.filter(Activity.NgayTao <= date_to)
    total_activities = activities_query.scalar() or 0
    
    avg_val = (total_activities / total_leads) if total_leads > 0 else 0.0
    return ActivityAverageResponse(avg_activities_per_lead=avg_val)

@router.get("/avg-response-time", response_model=ActivityResponseTimeResponse)
def get_avg_response_time(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get average response time (in hours) from Lead creation to first Activity.
    Calculation: difference in hours between Lead.NgayTao and MIN(Activity.NgayTao).
    """
    # Subquery to find the first activity per Lead
    first_activity_sub = db.query(
        Activity.LeadId.label("lead_id"),
        func.min(Activity.NgayTao).label("first_activity_time")
    ).filter(
        Activity.TrangThai == 1
    ).group_by(
        Activity.LeadId
    ).subquery()
    
    # Calculate response hours
    resp_hours = func.extract("epoch", first_activity_sub.c.first_activity_time - Lead.NgayTao) / 3600.0
    
    query = db.query(
        func.avg(resp_hours).label("avg_resp"),
        func.min(resp_hours).label("min_resp"),
        func.max(resp_hours).label("max_resp")
    ).join(
        first_activity_sub, Lead.Id == first_activity_sub.c.lead_id
    ).filter(
        first_activity_sub.c.first_activity_time >= Lead.NgayTao
    )
    
    if date_from:
        query = query.filter(Lead.NgayTao >= date_from)
    if date_to:
        query = query.filter(Lead.NgayTao <= date_to)
        
    result = query.first()
    
    if not result or result.avg_resp is None:
        return ActivityResponseTimeResponse(avg_response_hours=0.0, min_response_hours=0.0, max_response_hours=0.0)
        
    return ActivityResponseTimeResponse(
        avg_response_hours=float(result.avg_resp),
        min_response_hours=float(result.min_resp),
        max_response_hours=float(result.max_resp)
    )

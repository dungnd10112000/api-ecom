from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import date, datetime
from typing import List, Optional, Any
from app.database import get_db
from app.models import Customer, Order, Quotation, Taxonomy
from app.schemas import NewCustomersResponse, CustomerAreaStat, CustomerGroupStat, CustomerRepeatRateResponse, CustomerNewVsOldRevenueResponse
from app.routers.opportunities import get_date_trunc_field

router = APIRouter(prefix="/api/customers/stats", tags=["Customers"])

@router.get("/new-by-time", response_model=NewCustomersResponse)
def get_new_customers_by_time(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    group_by: Optional[str] = Query("month", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Get count of new customers registered over time."""
    # 1. Total count
    total_query = db.query(func.count(Customer.Id))
    if date_from:
        total_query = total_query.filter(Customer.NgayTao >= date_from)
    if date_to:
        total_query = total_query.filter(Customer.NgayTao <= date_to)
    total_customers = total_query.scalar() or 0

    # 2. Trend data
    trunc_field = get_date_trunc_field(Customer.NgayTao, group_by or "month")
    trend_query = db.query(
        trunc_field.label("period"),
        func.count(Customer.Id).label("count")
    )
    if date_from:
        trend_query = trend_query.filter(Customer.NgayTao >= date_from)
    if date_to:
        trend_query = trend_query.filter(Customer.NgayTao <= date_to)
        
    results = trend_query.group_by(trunc_field).order_by(trunc_field).all()
    
    trend_data = [
        {
            "period": r.period.strftime("%Y-%m-%d") if isinstance(r.period, (date, datetime)) else str(r.period),
            "count": r.count
        }
        for r in results
    ]

    return NewCustomersResponse(
        total_new_customers=total_customers,
        data=trend_data
    )

@router.get("/by-area", response_model=List[CustomerAreaStat])
def get_customers_by_area(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get customer counts grouped by province/city (TaxonomyType = 1)."""
    # Total count
    total_query = db.query(func.count(Customer.Id))
    if date_from:
        total_query = total_query.filter(Customer.NgayTao >= date_from)
    if date_to:
        total_query = total_query.filter(Customer.NgayTao <= date_to)
    total_count = total_query.scalar() or 0

    # Breakdown query
    query = db.query(
        Taxonomy.TieuDe.label("area_title"),
        func.count(Customer.Id).label("count")
    ).outerjoin(
        Taxonomy, Customer.AreaId == Taxonomy.Id
    )
    
    if date_from:
        query = query.filter(Customer.NgayTao >= date_from)
    if date_to:
        query = query.filter(Customer.NgayTao <= date_to)
        
    results = query.group_by(Taxonomy.TieuDe).order_by(func.count(Customer.Id).desc()).all()

    return [
        CustomerAreaStat(
            area=r.area_title or "Không xác định",
            customer_count=r.count,
            ratio=(r.count / total_count * 100.0) if total_count > 0 else 0.0
        )
        for r in results
    ]

@router.get("/by-group", response_model=CustomerGroupStat)
def get_customers_by_group(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get customer count breakdowns by ClassifyType and CustomerType."""
    # 1. Total count
    total_query = db.query(func.count(Customer.Id))
    if date_from:
        total_query = total_query.filter(Customer.NgayTao >= date_from)
    if date_to:
        total_query = total_query.filter(Customer.NgayTao <= date_to)
    total_count = total_query.scalar() or 0

    # 2. Classify Type (1=Company, 2=Individual)
    classify_query = db.query(
        Customer.ClassifyType.label("classify"),
        func.count(Customer.Id).label("count")
    )
    if date_from:
        classify_query = classify_query.filter(Customer.NgayTao >= date_from)
    if date_to:
        classify_query = classify_query.filter(Customer.NgayTao <= date_to)
    classify_res = classify_query.group_by(Customer.ClassifyType).all()

    classify_map = {1: "Doanh nghiệp (Enterprise)", 2: "Cá nhân (Individual)"}
    by_classify = [
        {
            "classify": classify_map.get(r.classify, "Không xác định"),
            "count": r.count,
            "ratio": (r.count / total_count * 100.0) if total_count > 0 else 0.0
        }
        for r in classify_res
    ]

    # 3. Customer Type (1=Normal Customer, 2=Agent/Partner)
    type_query = db.query(
        Customer.CustomerType.label("cust_type"),
        func.count(Customer.Id).label("count")
    )
    if date_from:
        type_query = type_query.filter(Customer.NgayTao >= date_from)
    if date_to:
        type_query = type_query.filter(Customer.NgayTao <= date_to)
    type_res = type_query.group_by(Customer.CustomerType).all()

    type_map = {1: "Khách hàng thường", 2: "Đại lý / Partner"}
    by_type = [
        {
            "customer_type": type_map.get(r.cust_type, "Không xác định"),
            "count": r.count,
            "ratio": (r.count / total_count * 100.0) if total_count > 0 else 0.0
        }
        for r in type_res
    ]

    return CustomerGroupStat(
        by_classify_type=by_classify,
        by_customer_type=by_type
    )

@router.get("/repeat-rate", response_model=CustomerRepeatRateResponse)
def get_customer_repeat_rate(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get customer repeat order rate.
    Repeat customer = Customer with >= 2 Orders in the selected period.
    """
    # Subquery: Count orders per customer
    customer_orders_sub = db.query(
        Quotation.PartnerId.label("customer_id"),
        func.count(Order.Id).label("order_count")
    ).join(
        Order, Order.SoHopDong == Quotation.SoHopDong
    )
    
    if date_from:
        customer_orders_sub = customer_orders_sub.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        customer_orders_sub = customer_orders_sub.filter(Order.NgayCapNhat <= date_to)
        
    customer_orders_sub = customer_orders_sub.group_by(Quotation.PartnerId).subquery()

    # Total customers with orders in period
    total_cust = db.query(func.count(customer_orders_sub.c.customer_id)).scalar() or 0
    
    # Repeat customers (order_count >= 2)
    repeat_cust = db.query(
        func.count(customer_orders_sub.c.customer_id)
    ).filter(
        customer_orders_sub.c.order_count >= 2
    ).scalar() or 0

    rate = (repeat_cust / total_cust * 100.0) if total_cust > 0 else 0.0

    return CustomerRepeatRateResponse(
        total_customers=total_cust,
        repeat_customers=repeat_cust,
        repeat_rate=rate
    )

@router.get("/revenue-new-vs-old", response_model=CustomerNewVsOldRevenueResponse)
def get_customer_new_vs_old_revenue(
    date_from: date,  # date_from is required for this calculation
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get revenue splits between new and returning customers.
    - New Customer = Created on or after date_from
    - Old Customer = Created before date_from
    """
    # 1. New Customers created in period
    new_cust_ids_query = db.query(Customer.Id).filter(Customer.NgayTao >= date_from)
    if date_to:
        new_cust_ids_query = new_cust_ids_query.filter(Customer.NgayTao <= date_to)
    new_cust_ids = [r[0] for r in new_cust_ids_query.all()]

    # 2. Revenue calculation for New Customers
    new_rev_query = db.query(
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("revenue"),
        func.count(Customer.Id.distinct()).label("count")
    ).join(
        Quotation, Order.SoHopDong == Quotation.SoHopDong
    ).join(
        Customer, Quotation.PartnerId == Customer.Id
    ).filter(
        Customer.Id.in_(new_cust_ids) if new_cust_ids else False
    )
    if date_from:
        new_rev_query = new_rev_query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        new_rev_query = new_rev_query.filter(Order.NgayCapNhat <= date_to)
    new_result = new_rev_query.first()

    # 3. Revenue calculation for Old Customers
    old_rev_query = db.query(
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("revenue"),
        func.count(Customer.Id.distinct()).label("count")
    ).join(
        Quotation, Order.SoHopDong == Quotation.SoHopDong
    ).join(
        Customer, Quotation.PartnerId == Customer.Id
    ).filter(
        Customer.NgayTao < date_from
    )
    if date_from:
        old_rev_query = old_rev_query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        old_rev_query = old_rev_query.filter(Order.NgayCapNhat <= date_to)
    old_result = old_rev_query.first()

    return CustomerNewVsOldRevenueResponse(
        new_customer_revenue=new_result.revenue if new_result else 0.0,
        old_customer_revenue=old_result.revenue if old_result else 0.0,
        new_customer_count=new_result.count if new_result else 0,
        old_customer_count=old_result.count if old_result else 0
    )

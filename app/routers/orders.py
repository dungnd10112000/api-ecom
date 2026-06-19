from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from datetime import date, datetime
from typing import List, Optional
from app.database import get_db
from app.models import Order, Quotation, Lead, RawCustomer, Customer, Taxonomy, UserFunction, LinkQuotationProduct, Product
from app.schemas import OrderStatsTime, RevenueSalesRepStat, RevenueProductStat, RevenueAreaStat, RevenueCustomerGroupStat, AverageTimeResponse
from app.routers.opportunities import get_date_trunc_field

router = APIRouter(prefix="/api/orders/stats", tags=["Orders"])

@router.get("/by-time", response_model=List[OrderStatsTime])
def get_orders_by_time(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    group_by: str = Query("month", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Get count of orders and total revenue (PhiDonHang) grouped by time periods."""
    trunc_field = get_date_trunc_field(Order.NgayCapNhat, group_by)
    
    query = db.query(
        trunc_field.label("period"),
        func.count(Order.Id).label("count"),
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("revenue")
    )
    
    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)
        
    results = query.group_by(trunc_field).order_by(trunc_field).all()
    
    return [
        OrderStatsTime(
            period=r.period.strftime("%Y-%m-%d") if isinstance(r.period, (date, datetime)) else str(r.period),
            order_count=r.count,
            total_revenue=r.revenue
        )
        for r in results
    ]

@router.get("/revenue-by-time", response_model=List[OrderStatsTime])
def get_revenue_by_time(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    group_by: str = Query("month", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """Get revenue (PhiDonHang) trend over time."""
    return get_orders_by_time(date_from, date_to, group_by, db)

@router.get("/revenue-by-sales-rep", response_model=List[RevenueSalesRepStat])
def get_revenue_by_sales_rep(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get revenue (PhiDonHang) grouped by sales rep (NguoiCapNhatId)."""
    query = db.query(
        UserFunction.FullName.label("rep_name"),
        UserFunction.UserName.label("username"),
        func.count(Order.Id).label("count"),
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("revenue")
    ).join(
        UserFunction, Order.NguoiCapNhatId == UserFunction.Id
    )
    
    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)
        
    results = query.group_by(UserFunction.FullName, UserFunction.UserName).order_by(func.sum(Order.PhiDonHang).desc()).all()
    
    return [
        RevenueSalesRepStat(
            rep_name=r.rep_name or "Unknown",
            username=r.username or "unknown",
            order_count=r.count,
            total_revenue=r.revenue
        )
        for r in results
    ]

@router.get("/revenue-by-product", response_model=List[RevenueProductStat])
def get_revenue_by_product(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    level: str = Query("group", regex="^(group|subgroup|product)$"),
    db: Session = Depends(get_db)
):
    """
    Get revenue grouped by product category or product.
    Join chain: Order -> Quotation (SoHopDong) -> LinkQuotationProduct -> Product -> Taxonomy
    """
    if level == "group":
        parent_tax = func.coalesce(Taxonomy.KhoaChaId, Taxonomy.Id)
        group_label = db.query(Taxonomy.TieuDe).filter(Taxonomy.Id == parent_tax).scalar_subquery()
        select_field = func.coalesce(group_label, "Unknown Category")
    elif level == "subgroup":
        select_field = func.coalesce(Taxonomy.TieuDe, "Unknown Category")
    else:
        select_field = func.coalesce(Product.TenSanPham, cast(Product.Id, String))

    query = db.query(
        select_field.label("label"),
        func.count(Order.Id.distinct()).label("count"),
        # Apportion order revenue equally or sum PhiDonHang? Usually sum of associated order revenue
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("revenue")
    ).join(
        Quotation, Order.SoHopDong == Quotation.SoHopDong
    ).join(
        LinkQuotationProduct, LinkQuotationProduct.QuotationId == Quotation.Id
    ).join(
        Product, LinkQuotationProduct.ProductId == Product.Id
    ).outerjoin(
        Taxonomy, Product.NhomThietBiId == Taxonomy.Id
    )

    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)

    results = query.group_by(select_field).order_by(func.sum(Order.PhiDonHang).desc()).all()

    return [
        RevenueProductStat(
            product_label=str(r.label),
            order_count=r.count,
            total_revenue=r.revenue
        )
        for r in results
    ]

@router.get("/product-performance")
def get_product_performance(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get top products performance (revenue, orders count, margin).
    Join chain: Order -> Quotation -> LinkQuotationProduct -> Product
    """
    query = db.query(
        Product.Id.label("id"),
        Product.SKU.label("sku"),
        Product.TenSanPham.label("name"),
        Product.GiaNhap.label("import_price"),
        Product.GiaBan.label("sale_price"),
        func.count(Order.Id.distinct()).label("order_count"),
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("total_revenue")
    ).join(
        Quotation, Order.SoHopDong == Quotation.SoHopDong
    ).join(
        LinkQuotationProduct, LinkQuotationProduct.QuotationId == Quotation.Id
    ).join(
        Product, LinkQuotationProduct.ProductId == Product.Id
    )

    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)

    results = query.group_by(
        Product.Id, Product.SKU, Product.TenSanPham, Product.GiaNhap, Product.GiaBan
    ).order_by(func.sum(Order.PhiDonHang).desc()).all()

    performance_list = []
    for r in results:
        margin = 0.0
        if r.sale_price and r.import_price and r.sale_price > 0:
            sp = float(r.sale_price)
            ip = float(r.import_price)
            margin = ((sp - ip) / sp) * 100.0
            
        performance_list.append({
            "id": r.id,
            "sku": r.sku or "N/A",
            "name": r.name or "Unnamed Product",
            "import_price": float(r.import_price or 0.0),
            "sale_price": float(r.sale_price or 0.0),
            "order_count": r.order_count,
            "total_revenue": float(r.total_revenue),
            "margin_percent": round(margin, 2)
        })
        
    return performance_list


@router.get("/revenue-by-area", response_model=List[RevenueAreaStat])
def get_revenue_by_area(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get revenue grouped by province/city.
    Join chain: Order -> Quotation (SoHopDong) -> Lead -> RawCustomer -> Taxonomy (AreaId, TaxonomyType=1)
    """
    # 1. Get total revenue for percentage
    total_rev_query = db.query(func.coalesce(func.sum(Order.PhiDonHang), 0))
    if date_from:
        total_rev_query = total_rev_query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        total_rev_query = total_rev_query.filter(Order.NgayCapNhat <= date_to)
    total_rev = float(total_rev_query.scalar() or 0.0)

    # 2. Get grouped breakdown
    query = db.query(
        Taxonomy.TieuDe.label("area_title"),
        func.count(Order.Id).label("count"),
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("revenue")
    ).join(
        Quotation, Order.SoHopDong == Quotation.SoHopDong
    ).join(
        Lead, Quotation.OpportunityId == Lead.Id  # Assuming Opportunity.Id connects or Quotation.OpportunityId joins with Lead
    ).join(
        RawCustomer, Lead.RawCustomerId == RawCustomer.Id
    ).join(
        Taxonomy, RawCustomer.AreaId == Taxonomy.Id
    ).filter(
        Taxonomy.TaxonomyType == 1
    )

    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)

    results = query.group_by(Taxonomy.TieuDe).order_by(func.sum(Order.PhiDonHang).desc()).all()

    return [
        RevenueAreaStat(
            area=r.area_title or "Unknown",
            order_count=r.count,
            total_revenue=r.revenue,
            ratio=(float(r.revenue) / total_rev * 100.0) if total_rev > 0 else 0.0
        )
        for r in results
    ]

@router.get("/revenue-by-customer-group", response_model=List[RevenueCustomerGroupStat])
def get_revenue_by_customer_group(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get revenue grouped by customer classification (ClassifyType).
    Join chain: Order -> Quotation -> Customer (PartnerId)
    """
    # 1. Total revenue
    total_rev_query = db.query(func.coalesce(func.sum(Order.PhiDonHang), 0))
    if date_from:
        total_rev_query = total_rev_query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        total_rev_query = total_rev_query.filter(Order.NgayCapNhat <= date_to)
    total_rev = float(total_rev_query.scalar() or 0.0)

    # 2. Breakdown
    query = db.query(
        Customer.ClassifyType.label("classify_type"),
        func.count(Order.Id.distinct()).label("order_count"),
        func.count(Customer.Id.distinct()).label("customer_count"),
        func.coalesce(func.sum(Order.PhiDonHang), 0).label("revenue")
    ).join(
        Quotation, Order.SoHopDong == Quotation.SoHopDong
    ).join(
        Customer, Quotation.PartnerId == Customer.Id
    )

    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)

    results = query.group_by(Customer.ClassifyType).all()

    classify_map = {
        1: "Doanh nghiệp (Enterprise)",
        2: "Cá nhân (Individual)"
    }

    return [
        RevenueCustomerGroupStat(
            customer_group=classify_map.get(r.classify_type, "Không xác định"),
            order_count=r.order_count,
            customer_count=r.customer_count,
            total_revenue=r.revenue,
            ratio=(float(r.revenue) / total_rev * 100.0) if total_rev > 0 else 0.0
        )
        for r in results
    ]

@router.get("/avg-deal-size", response_model=AverageTimeResponse)
def get_avg_deal_size(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Returns average, minimum, and maximum order values."""
    query = db.query(
        func.avg(Order.PhiDonHang).label("avg_val"),
        func.min(Order.PhiDonHang).label("min_val"),
        func.max(Order.PhiDonHang).label("max_val")
    )
    
    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)
        
    result = query.first()
    
    if not result or result.avg_val is None:
        return AverageTimeResponse(avg_hours=0.0, min_hours=0.0, max_hours=0.0)
        
    return AverageTimeResponse(
        # We reuse AverageTimeResponse schema format (repurposed for currency value)
        avg_hours=float(result.avg_val),
        min_hours=float(result.min_val),
        max_hours=float(result.max_val)
    )

@router.get("/avg-time-quotation-to-order", response_model=AverageTimeResponse)
def get_avg_time_quotation_to_order(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get average response time (in days) from Quotation creation to Order creation.
    Calculation: difference in days between Quotation.NgayTao and Order.NgayCapNhat.
    """
    # Extract days difference (in seconds / 86400)
    time_diff = func.extract("epoch", Order.NgayCapNhat - Quotation.NgayTao) / 86400.0
    
    query = db.query(
        func.avg(time_diff).label("avg_time"),
        func.min(time_diff).label("min_time"),
        func.max(time_diff).label("max_time")
    ).join(
        Quotation, Order.SoHopDong == Quotation.SoHopDong
    ).filter(
        Order.NgayCapNhat >= Quotation.NgayTao
    )
    
    if date_from:
        query = query.filter(Order.NgayCapNhat >= date_from)
    if date_to:
        query = query.filter(Order.NgayCapNhat <= date_to)
        
    result = query.first()
    
    if not result or result.avg_time is None:
        return AverageTimeResponse(avg_hours=0.0, min_hours=0.0, max_hours=0.0)
        
    return AverageTimeResponse(
        avg_hours=float(result.avg_time),
        min_hours=float(result.min_time),
        max_hours=float(result.max_time)
    )

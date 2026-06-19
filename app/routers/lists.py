from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import Optional, List
from app.database import get_db
from app.models import Customer, Order, Product, Lead

router = APIRouter(prefix="/api/raw", tags=["Raw Database Lists"])

@router.get("/customers")
def get_raw_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated and searchable list of Customer records."""
    query = db.query(Customer)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Customer.TenKhachHang.like(search_filter),
                Customer.SoDiDong.like(search_filter),
                Customer.Email.like(search_filter),
                Customer.DiaChi.like(search_filter)
            )
        )
        
    total = query.count()
    offset = (page - 1) * limit
    # Order by ID descending so newest records appear first
    results = query.order_by(desc(Customer.Id)).offset(offset).limit(limit).all()
    
    total_pages = (total + limit - 1) // limit
    
    return {
        "data": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages
        }
    }

@router.get("/orders")
def get_raw_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated and searchable list of Order records."""
    query = db.query(Order)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Order.SoPO.like(search_filter),
                Order.SoHopDong.like(search_filter),
                Order.MaVanDon.like(search_filter),
                Order.GhiChu.like(search_filter)
            )
        )
        
    total = query.count()
    offset = (page - 1) * limit
    results = query.order_by(desc(Order.Id)).offset(offset).limit(limit).all()
    
    total_pages = (total + limit - 1) // limit
    
    return {
        "data": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages
        }
    }

@router.get("/products")
def get_raw_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated and searchable list of Product records."""
    query = db.query(Product)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Product.SKU.like(search_filter),
                Product.TenSanPham.like(search_filter)
            )
        )
        
    total = query.count()
    offset = (page - 1) * limit
    results = query.order_by(desc(Product.Id)).offset(offset).limit(limit).all()
    
    total_pages = (total + limit - 1) // limit
    
    return {
        "data": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages
        }
    }

@router.get("/leads")
def get_raw_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated and searchable list of Lead records."""
    query = db.query(Lead)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Lead.TenKhachHang.like(search_filter),
                Lead.Email.like(search_filter),
                Lead.SoDienThoai.like(search_filter),
                Lead.DiaChi.like(search_filter)
            )
        )
        
    total = query.count()
    offset = (page - 1) * limit
    results = query.order_by(desc(Lead.Id)).offset(offset).limit(limit).all()
    
    total_pages = (total + limit - 1) // limit
    
    return {
        "data": results,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages
        }
    }

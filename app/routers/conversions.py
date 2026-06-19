from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List, Optional
from app.database import get_db
from app.models import Lead, Opportunity, Quotation, Order, UserFunction, LinkQuotationProduct, Product, Taxonomy
from app.schemas import ConversionRateResponse, EndToEndConversionResponse

router = APIRouter(prefix="/api/conversions/stats", tags=["Conversions"])

@router.get("/lead-to-opty", response_model=ConversionRateResponse)
def get_lead_to_opty_conversion(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get conversion rate from Lead to Opportunity.
    - Total Leads: Count of all leads
    - Converted: Leads that have at least 1 Opportunity (Opportunity.LeadId = Lead.Id)
    """
    # Total Leads
    total_query = db.query(func.count(Lead.Id))
    if date_from:
        total_query = total_query.filter(Lead.NgayTao >= date_from)
    if date_to:
        total_query = total_query.filter(Lead.NgayTao <= date_to)
    total_leads = total_query.scalar() or 0

    # Converted Leads
    converted_query = db.query(
        func.count(Lead.Id.distinct())
    ).join(
        Opportunity, Opportunity.LeadId == Lead.Id
    )
    if date_from:
        converted_query = converted_query.filter(Lead.NgayTao >= date_from)
    if date_to:
        converted_query = converted_query.filter(Lead.NgayTao <= date_to)
    converted_leads = converted_query.scalar() or 0

    rate = (converted_leads / total_leads * 100.0) if total_leads > 0 else 0.0

    return ConversionRateResponse(
        total=total_leads,
        converted=converted_leads,
        conversion_rate=rate
    )

@router.get("/opty-to-quotation", response_model=ConversionRateResponse)
def get_opty_to_quotation_conversion(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get conversion rate from Opportunity to Quotation.
    - Total Opportunities: Count of active opportunities
    - Converted: Opportunities that have at least 1 Quotation (Quotation.OpportunityId = Opportunity.Id)
    """
    total_query = db.query(func.count(Opportunity.Id)).filter(Opportunity.TrangThai == 1)
    if date_from:
        total_query = total_query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        total_query = total_query.filter(Opportunity.NgayTao <= date_to)
    total_optys = total_query.scalar() or 0

    converted_query = db.query(
        func.count(Opportunity.Id.distinct())
    ).join(
        Quotation, Quotation.OpportunityId == Opportunity.Id
    ).filter(
        Opportunity.TrangThai == 1
    )
    if date_from:
        converted_query = converted_query.filter(Opportunity.NgayTao >= date_from)
    if date_to:
        converted_query = converted_query.filter(Opportunity.NgayTao <= date_to)
    converted_optys = converted_query.scalar() or 0

    rate = (converted_optys / total_optys * 100.0) if total_optys > 0 else 0.0

    return ConversionRateResponse(
        total=total_optys,
        converted=converted_optys,
        conversion_rate=rate
    )

@router.get("/quotation-to-order", response_model=ConversionRateResponse)
def get_quotation_to_order_conversion(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get win rate of quotations (Quotation -> Order / Win).
    - Total Quotations: All quotations in confirmed/won/lost state
    - Converted: Quotations with status 4 (Close Won)
    """
    # Quotations in status 3 (Confirmed), 4 (Close Won), 5 (Close Lost)
    total_query = db.query(func.count(Quotation.Id)).filter(Quotation.TinhTrang.in_([3, 4, 5]))
    if date_from:
        total_query = total_query.filter(Quotation.NgayTao >= date_from)
    if date_to:
        total_query = total_query.filter(Quotation.NgayTao <= date_to)
    total_quotes = total_query.scalar() or 0

    won_query = db.query(func.count(Quotation.Id)).filter(Quotation.TinhTrang == 4)
    if date_from:
        won_query = won_query.filter(Quotation.NgayTao >= date_from)
    if date_to:
        won_query = won_query.filter(Quotation.NgayTao <= date_to)
    won_quotes = won_query.scalar() or 0

    rate = (won_quotes / total_quotes * 100.0) if total_quotes > 0 else 0.0

    return ConversionRateResponse(
        total=total_quotes,
        converted=won_quotes,
        conversion_rate=rate
    )

@router.get("/lead-to-order", response_model=EndToEndConversionResponse)
def get_lead_to_order_conversion(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get end-to-end conversion rate (Lead -> Opportunity -> Quotation (Won)).
    """
    # 1. Total Leads
    l_query = db.query(func.count(Lead.Id))
    if date_from:
        l_query = l_query.filter(Lead.NgayTao >= date_from)
    if date_to:
        l_query = l_query.filter(Lead.NgayTao <= date_to)
    total_leads = l_query.scalar() or 0

    # 2. Leads with Opportunities
    lo_query = db.query(func.count(Lead.Id.distinct())).join(
        Opportunity, Opportunity.LeadId == Lead.Id
    )
    if date_from:
        lo_query = lo_query.filter(Lead.NgayTao >= date_from)
    if date_to:
        lo_query = lo_query.filter(Lead.NgayTao <= date_to)
    leads_with_o = lo_query.scalar() or 0

    # 3. Leads with Quotations
    lq_query = db.query(func.count(Lead.Id.distinct())).join(
        Opportunity, Opportunity.LeadId == Lead.Id
    ).join(
        Quotation, Quotation.OpportunityId == Opportunity.Id
    )
    if date_from:
        lq_query = lq_query.filter(Lead.NgayTao >= date_from)
    if date_to:
        lq_query = lq_query.filter(Lead.NgayTao <= date_to)
    leads_with_q = lq_query.scalar() or 0

    # 4. Leads converted to Orders (Quotation Status = 4 Won)
    lwo_query = db.query(func.count(Lead.Id.distinct())).join(
        Opportunity, Opportunity.LeadId == Lead.Id
    ).join(
        Quotation, Quotation.OpportunityId == Opportunity.Id
    ).filter(
        Quotation.TinhTrang == 4
    )
    if date_from:
        lwo_query = lwo_query.filter(Lead.NgayTao >= date_from)
    if date_to:
        lwo_query = lwo_query.filter(Lead.NgayTao <= date_to)
    leads_won = lwo_query.scalar() or 0

    return EndToEndConversionResponse(
        total_leads=total_leads,
        leads_with_opportunities=leads_with_o,
        leads_with_quotations=leads_with_q,
        leads_won=leads_won,
        opty_conversion_rate=(leads_with_o / total_leads * 100.0) if total_leads > 0 else 0.0,
        quotation_conversion_rate=(leads_with_q / leads_with_o * 100.0) if leads_with_o > 0 else 0.0,
        win_rate=(leads_won / leads_with_q * 100.0) if leads_with_q > 0 else 0.0,
        end_to_end_conversion_rate=(leads_won / total_leads * 100.0) if total_leads > 0 else 0.0
    )

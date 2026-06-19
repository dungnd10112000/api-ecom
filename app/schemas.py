from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime, date
from decimal import Decimal

# Query Param Schemas
class DateFilterParams(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    group_by: Optional[str] = "month"  # day, week, month

# Common Response Schemas
class HealthCheckResponse(BaseModel):
    status: str
    database_connected: bool
    details: Optional[str] = None

class StatItem(BaseModel):
    label: str
    count: int
    ratio: Optional[float] = None

class LeadStatsByStatus(BaseModel):
    status: str
    count: int

class LeadStatsBySource(BaseModel):
    source: str
    count: int

class LeadSourceFilter(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None

class LeadSourceChildResponse(BaseModel):
    ten_nguon_con: str
    tong_lead: int
    children: Optional[List['LeadSourceChildResponse']] = None

class LeadSourceParentResponse(BaseModel):
    ten_nguon: str
    tong_lead: int
    children: Optional[List[LeadSourceChildResponse]] = None

class LeadSourceStatsResponse(BaseModel):
    success: bool
    filter: LeadSourceFilter
    data: List[LeadSourceParentResponse]

LeadSourceChildResponse.model_rebuild()

class LeadStatsByArea(BaseModel):
    area: str
    count: int

class LeadStatsBySalesRep(BaseModel):
    rep_name: str
    username: str
    count: int

class OpportunityTimeStat(BaseModel):
    period: str
    opportunity_count: int
    total_value: Decimal
    avg_value: Decimal

class OpportunitySalesRepStat(BaseModel):
    rep_name: str
    username: str
    opportunity_count: int
    total_value: Decimal
    avg_value: Decimal

class OpportunityProductStat(BaseModel):
    product_label: str
    opportunity_count: int
    total_value: Decimal

class PipelineTimeStat(BaseModel):
    period: str
    opportunity_count: int
    total_value: Decimal
    avg_value: Decimal

class PipelineSalesRepStat(BaseModel):
    rep_name: str
    username: str
    opportunity_count: int
    total_value: Decimal
    avg_value: Decimal
    max_value: Decimal

class FunnelStageStat(BaseModel):
    stage_id: int
    stage_name: str
    count: int
    total_value: Decimal
    count_ratio: float
    value_ratio: float

class AverageTimeResponse(BaseModel):
    avg_hours: float
    min_hours: float
    max_hours: float

class OrderStatsTime(BaseModel):
    period: str
    order_count: int
    total_revenue: Decimal

class RevenueSalesRepStat(BaseModel):
    rep_name: str
    username: str
    order_count: int
    total_revenue: Decimal

class RevenueProductStat(BaseModel):
    product_label: str
    order_count: int
    total_revenue: Decimal

class RevenueAreaStat(BaseModel):
    area: str
    order_count: int
    total_revenue: Decimal
    ratio: float

class RevenueCustomerGroupStat(BaseModel):
    customer_group: str
    order_count: int
    customer_count: int
    total_revenue: Decimal
    ratio: float

class ConversionRateResponse(BaseModel):
    total: int
    converted: int
    conversion_rate: float

class EndToEndConversionResponse(BaseModel):
    total_leads: int
    leads_with_opportunities: int
    leads_with_quotations: int
    leads_won: int
    opty_conversion_rate: float
    quotation_conversion_rate: float
    win_rate: float
    end_to_end_conversion_rate: float

class ActivityTypeStat(BaseModel):
    activity_type: str
    count: int

class ActivitySalesRepStat(BaseModel):
    rep_name: str
    username: str
    total_activities: int
    by_type: List[ActivityTypeStat]

class ActivityAverageResponse(BaseModel):
    avg_activities_per_lead: float

class ActivityResponseTimeResponse(BaseModel):
    avg_response_hours: float
    min_response_hours: float
    max_response_hours: float

class NewCustomersResponse(BaseModel):
    total_new_customers: int
    data: List[Any]  # Trend list

class CustomerAreaStat(BaseModel):
    area: str
    customer_count: int
    ratio: float

class CustomerGroupStat(BaseModel):
    by_classify_type: List[Any]
    by_customer_type: List[Any]

class CustomerRepeatRateResponse(BaseModel):
    total_customers: int
    repeat_customers: int
    repeat_rate: float

class CustomerNewVsOldRevenueResponse(BaseModel):
    new_customer_revenue: Decimal
    old_customer_revenue: Decimal
    new_customer_count: int
    old_customer_count: int

import sys
import os
sys.path.insert(0, os.getcwd())

from app.database import SessionLocal
from app.models import Customer, Lead, Opportunity, Quotation
from sqlalchemy import func

db = SessionLocal()
try:
    total_customers = db.query(func.count(Customer.Id)).scalar()
    enterprise_customers = db.query(func.count(Customer.Id)).filter(Customer.ClassifyType == 1).scalar()
    individual_customers = db.query(func.count(Customer.Id)).filter(Customer.ClassifyType == 2).scalar()
    null_customers = db.query(func.count(Customer.Id)).filter(Customer.ClassifyType.is_(None)).scalar()
    
    total_leads = db.query(func.count(Lead.Id)).scalar()
    leads_with_opty = db.query(func.count(Lead.Id)).join(Opportunity, Opportunity.LeadId == Lead.Id).scalar()
    
    print(f"Total customers: {total_customers}")
    print(f"Enterprise (1): {enterprise_customers}")
    print(f"Individual (2): {individual_customers}")
    print(f"Null/0 ClassifyType: {null_customers}")
    print(f"Total leads: {total_leads}")
    print(f"Leads with Opportunity: {leads_with_opty}")

finally:
    db.close()

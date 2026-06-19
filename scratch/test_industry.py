import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Lead, Opportunity, Quotation, LinkQuotationProduct, Product, Taxonomy
from sqlalchemy import func

def test_query():
    db = SessionLocal()
    try:
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
        ).distinct().subquery()

        results = db.query(
            subquery.c.category_title,
            func.count(subquery.c.lead_id).label("count")
        ).group_by(subquery.c.category_title).order_by(func.count(subquery.c.lead_id).desc()).all()

        print("Query Results:")
        for r in results:
            print(f"Category: {r.category_title or 'Chưa phân loại'}, Count: {r.count}")
    except Exception as e:
        print("Error executing query:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_query()

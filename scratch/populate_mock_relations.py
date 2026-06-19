from app.database import SessionLocal
from app.models import Order, Quotation, LinkQuotationProduct, Product
import random

def main():
    db = SessionLocal()
    try:
        orders = db.query(Order).all()
        products = db.query(Product).all()
        
        print(f"Found {len(orders)} orders and {len(products)} products.")
        
        if len(orders) > 0 and len(products) > 0:
            # 1. Clear existing Quotations and LinkQuotationProduct
            db.query(LinkQuotationProduct).delete()
            db.query(Quotation).delete()
            db.commit()
            print("Cleared existing mock Quotation & LinkQuotationProduct records.")
            
            # 2. Update orders to ensure they all have a SoHopDong, and generate Quotations
            quotations_created = 0
            links_created = 0
            for idx, order in enumerate(orders):
                if not order.SoHopDong or order.SoHopDong.strip() == "":
                    order.SoHopDong = f"HD-MOCK-{order.Id}"
                    
                # Create a Quotation
                quot = Quotation(
                    Id=100000 + idx,
                    OpportunityId=None,
                    PartnerId=None,
                    SoHopDong=order.SoHopDong,
                    TinhTrang=4, # Won
                    NgayTao=order.NgayCapNhat or order.NgayGuiSkype,
                    TongGiaTri=order.PhiDonHang
                )
                db.add(quot)
                db.flush() # Ensure the Quotation is inserted before linking products
                quotations_created += 1
                
                # Link to 1-3 random products
                num_prods = random.randint(1, 3)
                selected_prods = random.sample(products, num_prods)
                for prod in selected_prods:
                    link = LinkQuotationProduct(
                        QuotationId=quot.Id,
                        ProductId=prod.Id
                    )
                    db.add(link)
                    links_created += 1
                    
                if idx % 100 == 0:
                    db.commit()
                    
            db.commit()
            print(f"Successfully created {quotations_created} Quotations and {links_created} LinkQuotationProduct rows!")
        else:
            print("No orders or products found. Please run sync first.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    main()

import sys
import os
from sqlalchemy import create_engine, text

# Add current directory to path
sys.path.insert(0, os.getcwd())

passwords = ["123456", "postgres", "admin", ""]
ports = [5432, 5433]

connected = False
for port in ports:
    for pwd in passwords:
        try:
            url = f"postgresql://postgres:{pwd}@localhost:{port}/TCT_CRM"
            engine = create_engine(url, connect_args={"connect_timeout": 2})
            with engine.connect() as conn:
                print(f"SUCCESSFULLY CONNECTED to {port} with password '{pwd}'!")
                
                # Check lead sources
                print("\nTaxonomies with TaxonomyType = 3 (Sources):")
                print("-" * 50)
                query = text('SELECT "Id", "TieuDe", "TaxonomyType" FROM "Taxonomy" WHERE "TaxonomyType" = 3 ORDER BY "Id"')
                res = conn.execute(query)
                for r in res:
                    print(f"Id: {r[0]:<6} | Title: {r[1]:<25} | Type: {r[2]}")
                
                # Check lead counts by source
                print("\nLead counts by source:")
                print("-" * 50)
                query2 = text('''
                    SELECT t."TieuDe", COUNT(l."Id") as cnt 
                    FROM "Lead" l 
                    LEFT JOIN "Taxonomy" t ON l."SourceId" = t."Id" 
                    GROUP BY t."TieuDe"
                    ORDER BY cnt DESC
                ''')
                res2 = conn.execute(query2)
                for r in res2:
                    print(f"Source: {r[0] or 'Unknown':<30} | Count: {r[1]}")
                
                connected = True
                break
        except Exception as e:
            # print(f"Failed to connect to {port} with password '{pwd}': {e}")
            pass
    if connected:
        break

if not connected:
    print("Could not connect to any port.")

from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:123456@localhost:5433/TCT_CRM')
with engine.connect() as conn:
    print("Taxonomies with TaxonomyType = 3 (Sources):")
    print("-" * 50)
    query = text('SELECT "Id", "TieuDe", "TaxonomyType" FROM "Taxonomy" WHERE "TaxonomyType" = 3 ORDER BY "Id"')
    res = conn.execute(query)
    for r in res:
        print(f"Id: {r[0]:<6} | Title: {r[1]:<25} | Type: {r[2]}")
        
    print("\nAll Taxonomies in DB:")
    print("-" * 50)
    query2 = text('SELECT "Id", "TieuDe", "TaxonomyType" FROM "Taxonomy" ORDER BY "TaxonomyType", "Id"')
    res2 = conn.execute(query2)
    for r in res2:
        print(f"Id: {r[0]:<6} | Title: {r[1]:<25} | Type: {r[2]}")

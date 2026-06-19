from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# If schema is specified, set it in Metadata so tables are automatically mapped to it.
schema_name = settings.DB_SCHEMA if settings.DB_SCHEMA and settings.DB_SCHEMA != "public" else None
metadata = MetaData(schema=schema_name)

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={"client_encoding": "utf8"}
)

# Create SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Declarative Base
Base = declarative_base(metadata=metadata)

def get_db():
    """FastAPI dependency to inject database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

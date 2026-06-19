import os
os.environ["PGCLIENTENCODING"] = "utf-8"

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, Base, engine
from app.schemas import HealthCheckResponse
from app.routers import leads, opportunities, orders, conversions, activities, customers, sync, lists, reports
import uvicorn
import os

# Create database tables automatically if they don't exist
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables verified/created successfully.")
except Exception as e:
    print(f"Warning: Database tables creation failed (PostgreSQL credentials might not be configured yet): {str(e)}")

app = FastAPI(
    title="TCT_CRM E-commerce statistics API",
    description="Python FastAPI REST API for CRM analytical statistics, connecting to local/remote PostgreSQL database.",
    version="1.0.0"
)

# Set up CORS middleware to allow connection from frontend dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(leads.router)
app.include_router(opportunities.router)
app.include_router(orders.router)
app.include_router(conversions.router)
app.include_router(activities.router)
app.include_router(customers.router)
app.include_router(sync.router)
app.include_router(lists.router)
app.include_router(reports.router)

from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

@app.exception_handler(OperationalError)
def db_operational_error_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "Database connection failed. Please check your PostgreSQL credentials in the .env file.",
            "details": str(exc)
        }
    )

# Mount static folder for UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_index():
    """Serves the Database Preview Dashboard UI at the root path."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Welcome to TCT_CRM E-commerce Statistics API. Please visit /docs for API documentation.",
        "ui_status": "UI files (index.html) are being generated. Refresh in a moment."
    }

@app.get("/api/health", response_model=HealthCheckResponse, tags=["General"])
def health_check(db: Session = Depends(get_db)):
    """Verifies connection health with the PostgreSQL database."""
    try:
        db.execute(text("SELECT 1"))
        return HealthCheckResponse(status="healthy", database_connected=True)
    except Exception as e:
        return HealthCheckResponse(
            status="unhealthy",
            database_connected=False,
            details=str(e)
        )

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", 8000))
    host = os.getenv("APP_HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

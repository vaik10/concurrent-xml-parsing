from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import engine

app = FastAPI(
    title="Concurrent XML Processing Pipeline",
    version="1.0.0"
)


@app.get("/")
async def root():
    return {
        "service": "xml-processing-pipeline",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/db-health")
def db_health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "database": "connected"
    }

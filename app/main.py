from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine, get_db

from app.api.jobs import router as jobs_router

import app.models

from app.core.logging import configure_logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    Base.metadata.create_all(bind=engine)

    yield

app = FastAPI(
    title="Concurrent XML Processing Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(jobs_router)

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

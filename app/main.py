from fastapi import FastAPI

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
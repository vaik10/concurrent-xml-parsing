from fastapi import FastAPI

app = FastAPI(
    title="Concurrent XML Processing Pipeline",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
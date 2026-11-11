from fastapi import FastAPI

from app.api.demo import router as demo_router

app = FastAPI(title="Lab Control Panel", version="0.1.0")
app.include_router(demo_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lab-control-panel"}

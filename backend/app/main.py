from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.demo import dispose_database_engine, router as demo_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    dispose_database_engine()

app = FastAPI(title="Lab Control Panel", version="0.1.0", lifespan=lifespan)
app.include_router(demo_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lab-control-panel"}

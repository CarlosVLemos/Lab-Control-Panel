import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.demo import dispose_database_engine, router as demo_router
from app.db.session import create_database_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    dispose_database_engine()

app = FastAPI(title="Lab Control Panel", version="0.1.0", lifespan=lifespan)
app.include_router(demo_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "lab-control-panel"}


@app.get("/ready")
def readiness() -> dict[str, str]:
    expected_revision = os.environ.get("EXPECTED_ALEMBIC_REVISION")
    if not expected_revision:
        raise HTTPException(status_code=503, detail="API is not ready")

    engine = None
    try:
        engine = create_database_engine()
        with engine.connect() as connection:
            current_revision = connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    except (KeyError, SQLAlchemyError) as exc:
        raise HTTPException(status_code=503, detail="API is not ready") from exc
    finally:
        if engine is not None:
            engine.dispose()

    if current_revision != expected_revision:
        raise HTTPException(status_code=503, detail="API is not ready")
    return {"status": "ready", "service": "lab-control-panel"}

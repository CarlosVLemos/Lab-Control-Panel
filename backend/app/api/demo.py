"""Endpoints for the explicitly synthetic, persisted MVP demonstration."""

import os

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import create_database_engine, create_session_factory
from app.repositories.persistence import ConstraintViolation
from app.services.demo_experiments import DemoNotFound, create_demo_experiment, load_demo_experiment

router = APIRouter(prefix="/api/demo", tags=["demo"])
_engine = None
_session_factory = None


def _factory():
    global _engine, _session_factory
    try:
        if _session_factory is None:
            _engine = create_database_engine(os.environ["DATABASE_URL"])
            _session_factory = create_session_factory(_engine)
        return _session_factory
    except KeyError as exc:
        raise HTTPException(status_code=503, detail="Demo database is not configured") from exc


def dispose_database_engine() -> None:
    """Release the process-owned pool when FastAPI shuts down."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


@router.post("/experiments", status_code=201)
def create_experiment() -> dict:
    try:
        return create_demo_experiment(_factory())
    except HTTPException:
        raise
    except ConstraintViolation as exc:
        raise HTTPException(status_code=409, detail="Demo experiment could not be persisted") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Demo database is unavailable") from exc


@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str) -> dict:
    try:
        return load_demo_experiment(_factory(), experiment_id)
    except HTTPException:
        raise
    except DemoNotFound as exc:
        raise HTTPException(status_code=404, detail="Demo experiment was not found") from exc
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Demo database is unavailable") from exc

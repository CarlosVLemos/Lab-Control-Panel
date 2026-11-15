from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app import main


app = main.app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "lab-control-panel"}


def test_readiness_requires_database_at_expected_revision(monkeypatch):
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.scalar_one_or_none.return_value = "0001"
    monkeypatch.setenv("EXPECTED_ALEMBIC_REVISION", "0001")
    monkeypatch.setattr(main, "create_database_engine", lambda: engine)

    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "service": "lab-control-panel"}
    engine.dispose.assert_called_once_with()


def test_readiness_requires_expected_revision(monkeypatch):
    create_engine = MagicMock()
    monkeypatch.delenv("EXPECTED_ALEMBIC_REVISION", raising=False)
    monkeypatch.setattr(main, "create_database_engine", create_engine)

    response = TestClient(app).get("/ready")

    assert response.status_code == 503
    create_engine.assert_not_called()


def test_readiness_rejects_outdated_schema(monkeypatch):
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.scalar_one_or_none.return_value = "outdated"
    monkeypatch.setenv("EXPECTED_ALEMBIC_REVISION", "0001")
    monkeypatch.setattr(main, "create_database_engine", lambda: engine)

    response = TestClient(app).get("/ready")

    assert response.status_code == 503
    engine.dispose.assert_called_once_with()


def test_readiness_rejects_database_outage(monkeypatch):
    monkeypatch.setenv("EXPECTED_ALEMBIC_REVISION", "0001")

    def unavailable():
        raise OperationalError("connect", {}, Exception("unavailable"))

    monkeypatch.setattr(main, "create_database_engine", unavailable)

    response = TestClient(app).get("/ready")

    assert response.status_code == 503

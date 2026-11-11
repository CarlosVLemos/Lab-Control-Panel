"""HTTP integration checks for the persisted deterministic demo."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from test_postgresql_persistence import postgres


def test_demo_post_get_is_idempotent_and_does_not_reexecute(postgres, monkeypatch):
    """A fresh client can read rows after the fixture execution path is disabled."""
    with TestClient(app) as client:
        created = client.post("/api/demo/experiments")
        assert created.status_code == 201
        report = created.json()
        assert len(report["cases"]) == 6
        assert report["summary"] == {
            "baseline": {"passed": 2, "total": 6},
            "candidate": {"passed": 6, "total": 6},
        }

    def fixture_must_not_run():
        pytest.fail("GET/repeated POST must load persisted output, not run classifiers")

    monkeypatch.setattr("app.services.demo_experiments._fixture_report", fixture_must_not_run)
    with TestClient(app) as restarted_client:
        loaded = restarted_client.get("/api/demo/experiments/demo-support-intents-v1")
        repeated = restarted_client.post("/api/demo/experiments")
    assert loaded.status_code == 200
    assert loaded.json() == report
    assert repeated.status_code == 201
    assert repeated.json() == report


def test_demo_database_outage_is_explicit(postgres, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://lcp:lcp@127.0.0.1:1/lcp_test")
    response = TestClient(app).get("/api/demo/experiments/missing")
    assert response.status_code == 503
    assert response.json()["detail"] == "Demo database is unavailable"

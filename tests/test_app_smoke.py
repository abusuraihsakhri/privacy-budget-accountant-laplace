"""API and CLI smoke checks against the actual installed application."""
import json
from fastapi.testclient import TestClient

from agents.api import app
from cli import main


def test_browser_and_health_routes():
    client = TestClient(app)
    assert client.get("/").status_code == 200
    assert "Laplace privacy budget calculator" in client.get("/").text
    assert "function createLedger" in client.get("/app.js").text
    assert client.get("/health").json()["status"] == "HEALTHY"


def test_legacy_audit_route():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "TEST-123", "target_identifier": "SAFE-IDENTIFIER",
        "primary_metric": 5, "secondary_metric": 2,
        "status_descriptor": "NOMINAL",
    })
    assert response.status_code == 200
    assert response.json()["total_alerts"] == 0


def test_prohibited_identifier_rejected_with_client_error():
    client = TestClient(app)
    response = client.post("/api/audit", json={
        "task_id": "MRN-123456", "target_identifier": "SAFE-ID",
        "primary_metric": 5,
    })
    assert response.status_code == 422


def test_laplace_cli(capsys):
    assert main(["laplace", "--total-epsilon", "1", "--epsilon", "0.2", "--value", "10", "--sensitivity", "1"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["scale"] == 5
    assert output["spent_epsilon"] == 0.2
    assert main(["laplace", "--total-epsilon", "1", "--epsilon", "2", "--value", "10", "--sensitivity", "1"]) == 2

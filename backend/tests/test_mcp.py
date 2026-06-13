import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.auth import get_current_user
from app.models.user import User
from app.core.database import SessionLocal
from app.models.patient import Patient

# Mock user dependency to bypass actual authentication database lookup
def override_get_current_user():
    return User(
        id="550e8400-e29b-41d4-a716-446655440000",
        phone="9876543200",
        full_name="Test Doctor",
        role="doctor",
        is_active=True
    )

@pytest.fixture(autouse=True)
def setup_auth():
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.clear()

client = TestClient(app)

@pytest.fixture
def test_patient_id():
    db = SessionLocal()
    try:
        patient = db.query(Patient).first()
        if patient:
            return str(patient.id)
        return "3bf5cb06-b36a-41e9-b0a2-7c57fdeb1e2f"  # fallback UUID
    finally:
        db.close()

def test_mcp_dashboard_summary():
    response = client.get("/api/v1/mcp/dashboard_summary")
    assert response.status_code == 200
    json_data = response.json()
    assert "tool" in json_data
    assert json_data["tool"] == "get_dashboard_summary"
    assert "result" in json_data
    result = json_data["result"]
    assert isinstance(result, dict)

def test_mcp_search_patient(test_patient_id):
    response = client.get(f"/api/v1/mcp/search_patient?patient_id={test_patient_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert "tool" in json_data
    assert json_data["tool"] == "search_patient"
    assert "result" in json_data
    result = json_data["result"]
    assert isinstance(result, dict)
    if "error" not in result:
        assert "name" in result
        assert "id" in result

def test_mcp_get_patient_risk(test_patient_id):
    response = client.get(f"/api/v1/mcp/get_patient_risk?patient_id={test_patient_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert "tool" in json_data
    assert json_data["tool"] == "get_patient_risk"
    assert "result" in json_data
    result = json_data["result"]
    assert isinstance(result, dict)
    if "error" not in result:
        assert "risk_score" in result
        assert "risk_level" in result

def test_mcp_get_patient_prescriptions(test_patient_id):
    response = client.get(f"/api/v1/mcp/get_patient_prescriptions?patient_id={test_patient_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert "tool" in json_data
    assert json_data["tool"] == "get_patient_prescriptions"
    assert "result" in json_data
    result = json_data["result"]
    assert isinstance(result, dict)
    if "error" not in result:
        assert "prescriptions" in result
        assert isinstance(result["prescriptions"], list)

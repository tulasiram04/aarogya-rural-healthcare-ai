import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.auth import get_current_user

def test_health_check():
    # Clear overrides first to test clean authentication
    app.dependency_overrides.clear()
    
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
    assert "service" in json_data
    assert "version" in json_data

def test_protected_route_rejects_unauthorized():
    app.dependency_overrides.clear()
    client = TestClient(app)
    
    # Access a protected endpoint without auth header
    response = client.get("/api/v1/patients/")
    # OAuth2PasswordBearer raises 401 Unauthorized if no credentials provided
    assert response.status_code == 401

def test_protected_route_accepts_valid_auth():
    from app.models.user import User
    
    def override_get_current_user():
        return User(
            id="550e8400-e29b-41d4-a716-446655440000",
            phone="9876543200",
            full_name="Dr. Test",
            role="doctor",
            is_active=True
        )
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    
    response = client.get("/api/v1/patients/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Clear overrides after test is done
    app.dependency_overrides.clear()

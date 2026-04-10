import pytest
import os
from fastapi.testclient import TestClient
from app.main import app

def test_api_no_key_set(api_client):
    """When SHARPEI_API_KEY is not set, API should be accessible without header."""
    # Ensure environment variable is not set for this test
    if "SHARPEI_API_KEY" in os.environ:
        del os.environ["SHARPEI_API_KEY"]
    
    response = api_client.get("/api/tasks")
    assert response.status_code == 200

def test_api_with_key_set_missing_header(monkeypatch):
    """When SHARPEI_API_KEY is set, API should return 401 if header is missing."""
    monkeypatch.setenv("SHARPEI_API_KEY", "test-secret-key")
    
    # We need a new client because middleware might be initialized or depend on env at startup
    # Actually FastAPI middleware checks env on each request in the proposed implementation
    client = TestClient(app)
    
    response = client.get("/api/tasks")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized: Invalid or missing API Key"

def test_api_with_key_set_wrong_header(monkeypatch):
    """When SHARPEI_API_KEY is set, API should return 401 if header is wrong."""
    monkeypatch.setenv("SHARPEI_API_KEY", "test-secret-key")
    client = TestClient(app)
    
    response = client.get("/api/tasks", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401

def test_api_with_key_set_correct_header(monkeypatch):
    """When SHARPEI_API_KEY is set, API should return 200 if header is correct."""
    monkeypatch.setenv("SHARPEI_API_KEY", "test-secret-key")
    client = TestClient(app)
    
    response = client.get("/api/tasks", headers={"X-API-Key": "test-secret-key"})
    # It might be 200 (empty list) or other success code depending on DB state
    assert response.status_code == 200

def test_non_api_routes_no_key_required(monkeypatch):
    """Routes not starting with /api should not require a key even if set."""
    monkeypatch.setenv("SHARPEI_API_KEY", "test-secret-key")
    client = TestClient(app)
    
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

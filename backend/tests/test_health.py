"""Unit and integration tests for backend health and capabilities."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """Verify that root endpoint returns service overview."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "SchemaSense AI"
    assert data["version"] == "0.1.0"
    assert "health" in data
    assert "capabilities" in data


def test_health_endpoint(client: TestClient) -> None:
    """Verify that /api/health returns accurate status and timing."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert data["service"] == "SchemaSense AI API"
    assert data["environment"] == "development"
    assert "timestamp" in data
    assert isinstance(data["uptime_seconds"], (int, float))
    assert data["uptime_seconds"] >= 0.0


def test_capabilities_endpoint(client: TestClient) -> None:
    """Verify that /api/capabilities accurately reports Phase 1 capability matrix."""
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "SchemaSense AI"
    assert "capabilities" in data

    caps = data["capabilities"]
    # Phase 1 & 3 features active
    assert caps["health_check"] is True
    assert caps["capabilities_discovery"] is True
    assert caps["schema_introspection"] is True
    assert caps["database_registration"] is True
    assert caps["sqlite_upload"] is True
    assert caps["relationship_discovery"] is True
    assert caps["table_preview"] is True
    assert caps["schema_context_generation"] is True

    # Phase 4 features active
    assert caps["natural_language_sql"] is True
    assert caps["query_history_archiving"] is True

    # Phase 5 features active (execution sandbox and self-correction loop)
    assert caps["sql_execution"] is True
    assert caps["sql_self_correction"] is True

    # Supported targets
    assert "postgresql" in data["supported_dialects"]
    assert "sqlite" in data["supported_dialects"]
    assert "local" in data["supported_ai_providers"]


def test_cors_headers(client: TestClient) -> None:
    """Verify that explicit CORS headers are returned for allowed origins."""
    origin = "http://localhost:5173"
    response = client.options(
        "/api/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin

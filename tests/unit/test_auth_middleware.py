import pytest
from starlette.testclient import TestClient

from studob.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_no_auth_required(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_root_no_auth_required(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_api_endpoints_accessible_without_auth_when_disabled(client):
    resp = client.get("/api/v1/students/")
    assert resp.status_code in (200, 404, 422, 500)
    assert resp.status_code != 401

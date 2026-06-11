"""
Tests for the API Gateway proxy routes.
All upstream services are mocked with httpx.
"""
import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

client = TestClient(app)


def _mock_upstream(status_code: int = 200, body: dict = None):
    """Return a fake httpx.Response-like mock."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = json.dumps(body or {"ok": True}).encode()
    resp.headers = {"content-type": "application/json"}
    return resp


# ---------------------------------------------------------------------------
# /kcal/predict  →  kcal:8001/analyze
# ---------------------------------------------------------------------------

def test_kcal_predict_proxied():
    upstream = _mock_upstream(200, {"total_kcal": 543.3, "items": [], "message": "ok"})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.post(
            "/kcal/predict",
            json={"text": "200g of chicken"},
            headers={"Authorization": "Bearer clesecrete"},
        )

    assert resp.status_code == 200
    assert resp.json()["total_kcal"] == 543.3


def test_kcal_predict_upstream_error():
    upstream = _mock_upstream(502, {"detail": "upstream down"})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.post(
            "/kcal/predict",
            json={"text": "200g of chicken"},
            headers={"Authorization": "Bearer clesecrete"},
        )

    assert resp.status_code == 502


# ---------------------------------------------------------------------------
# /kcal/analyze-image  →  kcal:8001/analyze-image
# ---------------------------------------------------------------------------

def test_kcal_analyze_image_proxied():
    upstream = _mock_upstream(200, {"total_kcal": 300.0, "items": [], "message": "ok"})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.post.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.post(
            "/kcal/analyze-image",
            headers={"Authorization": "Bearer clesecrete"},
            files={"file": ("meal.jpg", b"fake-image", "image/jpeg")},
        )

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /meal/{path}  →  meal:8003
# ---------------------------------------------------------------------------

def test_meal_proxy_get():
    upstream = _mock_upstream(200, [{"id": 1, "nom": "Riz"}])

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.request.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.get("/meal/aliments")

    assert resp.status_code == 200


def test_meal_proxy_post():
    upstream = _mock_upstream(200, {"id": 42, "nom": "Poulet"})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.request.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.post("/meal/aliments", json={"nom": "Poulet", "calories_100g": 165})

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /auth/{path}  →  auth:8004
# ---------------------------------------------------------------------------

def test_auth_proxy_login():
    upstream = _mock_upstream(200, {"success": True, "user_id": 1})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.request.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "secret123"},
        )

    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_auth_proxy_unauthorized():
    upstream = _mock_upstream(401, {"detail": "Email ou mot de passe incorrect."})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.request.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "badpass"},
        )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /etl/{path}  →  etl:8002
# ---------------------------------------------------------------------------

def test_etl_proxy_health():
    upstream = _mock_upstream(200, {"status": "ok", "service": "healthai_etl"})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.request.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.get("/etl/health")

    assert resp.status_code == 200


def test_etl_proxy_run():
    upstream = _mock_upstream(200, {"status": "started"})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.request.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.post("/etl/etl/run")

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /admin/{path}  →  admin:8005
# ---------------------------------------------------------------------------

def test_admin_proxy_get():
    upstream = _mock_upstream(200, {"users": []})

    with patch("app.routes.httpx.AsyncClient") as mock_cls:
        mock_http = AsyncMock()
        mock_http.request.return_value = upstream
        mock_cls.return_value.__aenter__.return_value = mock_http

        resp = client.get("/admin/users")

    assert resp.status_code == 200

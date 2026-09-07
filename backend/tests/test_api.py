import io

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def inspector_token(client):
    res = client.post("/api/v1/auth/login", json={"username": "inspector", "password": "inspector123"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def admin_token(client):
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    return res.json()["access_token"]


# ------------------------------------------------------------------------------
# 1. Health & Root Tests
# ------------------------------------------------------------------------------
def test_root_and_health(client):
    res_root = client.get("/")
    assert res_root.status_code == 200
    data = res_root.json()
    assert data["rule_version"].startswith("LMPC-2011")

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"


# ------------------------------------------------------------------------------
# 2. Authentication & 2-Role RBAC Tests
# ------------------------------------------------------------------------------
def test_auth_login_inspector(client):
    res = client.post("/api/v1/auth/login", json={"username": "inspector", "password": "inspector123"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "inspector"
    assert "access_token" in data
    assert data["username"] == "inspector"
    assert data["full_name"] == "Field Officer Sharma"


def test_auth_login_admin(client):
    res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "admin"
    assert "access_token" in data
    assert data["username"] == "admin"
    assert data["full_name"] == "Enforcement Director Verma"


def test_auth_login_invalid(client):
    res = client.post("/api/v1/auth/login", json={"username": "inspector", "password": "wrongpassword"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password"


def test_auth_me_with_token(client, inspector_token, admin_token):
    # Test inspector
    res_insp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {inspector_token}"})
    assert res_insp.status_code == 200
    assert res_insp.json()["role"] == "inspector"
    assert res_insp.json()["username"] == "inspector"

    # Test admin
    res_adm = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_adm.status_code == 200
    assert res_adm.json()["role"] == "admin"
    assert res_adm.json()["username"] == "admin"


# ------------------------------------------------------------------------------
# 3. History & Filtering Tests Against Dummy Data
# ------------------------------------------------------------------------------
def test_history_list_all(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}
    res = client.get("/api/v1/history?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 6
    assert len(data["items"]) >= 6
    for item in data["items"]:
        assert item["overall_status"] in ["PASS", "FAIL", "REVIEW_REQUIRED"]
        assert item["rule_version"] == "LMPC-2011-v1.0"


def test_history_filter_by_status(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}

    # Filter PASS
    res_pass = client.get("/api/v1/history?status=PASS", headers=headers)
    assert res_pass.status_code == 200
    for item in res_pass.json()["items"]:
        assert item["overall_status"] == "PASS"

    # Filter FAIL
    res_fail = client.get("/api/v1/history?status=FAIL", headers=headers)
    assert res_fail.status_code == 200
    for item in res_fail.json()["items"]:
        assert item["overall_status"] == "FAIL"

    # Filter REVIEW_REQUIRED
    res_rev = client.get("/api/v1/history?status=REVIEW_REQUIRED", headers=headers)
    assert res_rev.status_code == 200
    for item in res_rev.json()["items"]:
        assert item["overall_status"] == "REVIEW_REQUIRED"


def test_history_filter_by_category(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}

    # Filter bulk_exempt
    res = client.get("/api/v1/history?category=bulk_exempt", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any("Cement" in item["product_name"] for item in data["items"])


def test_history_filter_by_product_name(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}
    res = client.get("/api/v1/history?product_name=Dark%20Fantasy", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert "Dark Fantasy" in data["items"][0]["product_name"]


def test_history_detail(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}
    list_res = client.get("/api/v1/history?page=1&page_size=1", headers=headers)
    scan_id = list_res.json()["items"][0]["scan_id"]

    res = client.get(f"/api/v1/history/{scan_id}", headers=headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["scan_id"] == scan_id
    assert "compliance_results" in detail
    assert len(detail["compliance_results"]) > 0
    for r in detail["compliance_results"]:
        assert r["status"] in ["PASS", "FAIL", "REVIEW_REQUIRED"]
        assert r["rule_version"].startswith("LMPC-2011")


# ------------------------------------------------------------------------------
# 4. Universal Search Tests Against Dummy Data
# ------------------------------------------------------------------------------
def test_search_by_brand(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}
    res = client.get("/api/v1/search?q=Sunfeast", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 1
    assert any("Sunfeast" in r["product_name"] for r in data["results"])


def test_search_by_product_name(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}
    res = client.get("/api/v1/search?q=Maggi", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 1
    assert any("Maggi" in r["product_name"] for r in data["results"])


def test_search_with_status_filter(client, inspector_token):
    headers = {"Authorization": f"Bearer {inspector_token}"}
    res = client.get("/api/v1/search?q=Savlon&status=REVIEW_REQUIRED", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 1
    assert data["results"][0]["overall_status"] == "REVIEW_REQUIRED"


# ------------------------------------------------------------------------------
# 5. Dashboard & Report Tests
# ------------------------------------------------------------------------------
def test_dashboard_stats(client):
    res = client.get("/api/v1/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_scans"] >= 6
    assert data["pass_count"] >= 3
    assert data["fail_count"] >= 2
    assert data["review_required_count"] >= 1
    assert isinstance(data["compliance_rate_pct"], float)
    assert len(data["most_common_violations"]) >= 1


def test_scan_stub(client):
    mock_img = io.BytesIO(b"dummy image bytes")
    mock_img.name = "test.jpg"
    files = {"file": ("test.jpg", mock_img, "image/jpeg")}
    res = client.post("/api/v1/scan", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] in ["PASS", "FAIL", "REVIEW_REQUIRED"]
    assert data["rule_version"] == "LMPC-2011-v1.0"

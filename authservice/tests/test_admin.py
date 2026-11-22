from app.models import Role
from tests.conftest import auth_header, login, make_user


def test_only_admins_manage_users(client):
    make_user("student@example.com")
    headers = auth_header(client, "student@example.com")
    r = client.get("/api/auth/users", headers=headers)
    assert r.status_code == 403 and r.json()["code"] == "FORBIDDEN"


def test_admin_lists_and_creates_users(client):
    make_user("admin@example.com", roles=(Role.ADMIN,))
    make_user("s1@example.com")
    make_user("s2@example.com")
    headers = auth_header(client, "admin@example.com")

    r = client.post("/api/auth/users", headers=headers,
                    json={"email": "prof@example.com", "password": "Lectur3r-pass", "roles": ["LECTURER"]})
    assert r.status_code == 201
    assert r.json()["roles"] == ["LECTURER"] and r.json()["emailVerified"] is True
    assert login(client, "prof@example.com", "Lectur3r-pass").status_code == 200

    page = client.get("/api/auth/users", headers=headers, params={"role": "STUDENT", "size": 1}).json()
    assert page["page"] == {"size": 1, "number": 0, "totalElements": 2, "totalPages": 2}
    assert len(page["content"]) == 1

    found = client.get("/api/auth/users", headers=headers, params={"q": "prof"}).json()
    assert [u["email"] for u in found["content"]] == ["prof@example.com"]


def test_admin_disables_user_and_revokes_sessions(client):
    make_user("admin@example.com", roles=(Role.ADMIN,))
    student = make_user("s1@example.com")
    headers = auth_header(client, "admin@example.com")
    session = login(client, "s1@example.com").json()

    r = client.patch(f"/api/auth/users/{student.id}", headers=headers, json={"status": "DISABLED"})
    assert r.status_code == 200 and r.json()["status"] == "DISABLED"
    r = login(client, "s1@example.com")
    assert r.status_code == 403 and r.json()["code"] == "ACCOUNT_DISABLED"
    assert client.post("/api/auth/refresh", json={"refreshToken": session["refreshToken"]}).status_code == 401
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {session['accessToken']}"})
    assert me.status_code == 401

    r = client.patch(f"/api/auth/users/{student.id}", headers=headers,
                     json={"status": "ACTIVE", "roles": ["STUDENT", "LECTURER"]})
    assert r.json()["roles"] == ["LECTURER", "STUDENT"]
    assert login(client, "s1@example.com").status_code == 200


def test_admin_cannot_lock_themselves_out(client):
    admin = make_user("admin@example.com", roles=(Role.ADMIN,))
    headers = auth_header(client, "admin@example.com")
    for body in ({"status": "DISABLED"}, {"roles": ["LECTURER"]}):
        r = client.patch(f"/api/auth/users/{admin.id}", headers=headers, json=body)
        assert r.status_code == 409 and r.json()["code"] == "SELF_LOCKOUT"


def test_unknown_user_returns_404(client):
    make_user("admin@example.com", roles=(Role.ADMIN,))
    headers = auth_header(client, "admin@example.com")
    r = client.get("/api/auth/users/00000000-0000-0000-0000-000000000000", headers=headers)
    assert r.status_code == 404 and r.json()["code"] == "USER_NOT_FOUND"

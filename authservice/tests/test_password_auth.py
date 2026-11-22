import jwt

from app.config import settings
from tests.conftest import PASSWORD, auth_header, login, make_user, token_from


def test_register_verify_then_login(client, outbox):
    r = client.post("/api/auth/register", json={"email": "Alice@Example.com", "password": PASSWORD})
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "alice@example.com"
    assert body["roles"] == ["STUDENT"]
    assert body["emailVerified"] is False
    assert "passwordHash" not in body

    # Email non vérifié : connexion refusée même avec le bon mot de passe
    r = login(client, "alice@example.com")
    assert r.status_code == 403 and r.json()["code"] == "EMAIL_NOT_VERIFIED"

    assert len(outbox) == 1 and outbox[0][0] == "alice@example.com"
    token = token_from(outbox[0][2])
    assert client.post("/api/auth/verify-email", json={"token": token}).status_code == 204
    r = client.post("/api/auth/verify-email", json={"token": token})
    assert r.status_code == 400 and r.json()["code"] == "TOKEN_INVALID"  # usage unique

    r = login(client, "ALICE@example.com")
    assert r.status_code == 200
    tokens = r.json()
    assert tokens["tokenType"] == "Bearer" and tokens["expiresIn"] == 3600
    claims = jwt.decode(tokens["accessToken"], settings.jwt_secret, algorithms=["HS256"],
                        issuer="campusconnect-auth")
    assert claims["sub"] == body["id"] and claims["roles"] == ["STUDENT"]
    assert claims["email"] == "alice@example.com"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['accessToken']}"})
    assert me.status_code == 200
    assert me.json()["emailVerified"] is True and me.json()["faceEnrolled"] is False


def test_register_rejects_duplicates_and_invalid_input(client):
    make_user("bob@example.com")
    r = client.post("/api/auth/register", json={"email": "BOB@example.com", "password": PASSWORD})
    assert r.status_code == 409 and r.json()["code"] == "EMAIL_TAKEN"

    r = client.post("/api/auth/register", json={"email": "not-an-email", "password": "short"})
    assert r.status_code == 400
    assert r.headers["content-type"] == "application/problem+json"
    assert {e["field"] for e in r.json()["errors"]} == {"email", "password"}


def test_resend_verification_does_not_reveal_accounts(client, outbox):
    make_user("unverified@example.com", verified=False)
    assert client.post("/api/auth/verify-email/resend", json={"email": "nobody@example.com"}).status_code == 202
    assert outbox == []
    assert client.post("/api/auth/verify-email/resend", json={"email": "unverified@example.com"}).status_code == 202
    assert len(outbox) == 1


def test_wrong_password_and_lockout(client):
    make_user("carol@example.com")
    for _ in range(settings.max_failed_attempts):
        r = login(client, "carol@example.com", "wrong-password")
        assert r.status_code == 401 and r.json()["code"] == "BAD_CREDENTIALS"

    r = login(client, "carol@example.com")  # bon mot de passe, mais compte verrouillé
    assert r.status_code == 423 and r.json()["code"] == "ACCOUNT_LOCKED"
    assert int(r.headers["Retry-After"]) > 0

    r = login(client, "ghost@example.com", "whatever")  # email inconnu : même réponse qu'un mauvais mot de passe
    assert r.status_code == 401 and r.json()["code"] == "BAD_CREDENTIALS"


def test_refresh_rotation_and_reuse_detection(client):
    make_user("dan@example.com")
    first = login(client, "dan@example.com").json()

    r = client.post("/api/auth/refresh", json={"refreshToken": first["refreshToken"]})
    assert r.status_code == 200
    second = r.json()
    assert second["refreshToken"] != first["refreshToken"]

    # Réutiliser l'ancien jeton = vol probable : toutes les sessions sont révoquées
    r = client.post("/api/auth/refresh", json={"refreshToken": first["refreshToken"]})
    assert r.status_code == 401 and r.json()["code"] == "TOKEN_REUSED"
    r = client.post("/api/auth/refresh", json={"refreshToken": second["refreshToken"]})
    assert r.status_code == 401


def test_logout_revokes_refresh_token(client):
    make_user("eve@example.com")
    tokens = login(client, "eve@example.com").json()
    other_device = login(client, "eve@example.com").json()
    assert client.post("/api/auth/logout", json={"refreshToken": tokens["refreshToken"]}).status_code == 204
    r = client.post("/api/auth/refresh", json={"refreshToken": tokens["refreshToken"]})
    assert r.status_code == 401 and r.json()["code"] == "TOKEN_REVOKED"
    # un jeton déconnecté n'est pas un vol : les autres sessions restent valides
    assert client.post("/api/auth/refresh", json={"refreshToken": other_device["refreshToken"]}).status_code == 200


def test_forgot_and_reset_password(client, outbox):
    make_user("frank@example.com")
    old_session = login(client, "frank@example.com").json()

    assert client.post("/api/auth/password/forgot", json={"email": "nobody@example.com"}).status_code == 202
    assert outbox == []
    assert client.post("/api/auth/password/forgot", json={"email": "frank@example.com"}).status_code == 202
    token = token_from(outbox[0][2])

    r = client.post("/api/auth/password/reset", json={"token": token, "newPassword": "N3w-password!"})
    assert r.status_code == 204
    assert login(client, "frank@example.com").status_code == 401
    assert login(client, "frank@example.com", "N3w-password!").status_code == 200
    # les anciennes sessions sont coupées
    assert client.post("/api/auth/refresh", json={"refreshToken": old_session["refreshToken"]}).status_code == 401
    r = client.post("/api/auth/password/reset", json={"token": token, "newPassword": "Other-pass1!"})
    assert r.status_code == 400


def test_change_password(client):
    make_user("gina@example.com")
    headers = auth_header(client, "gina@example.com")
    r = client.put("/api/auth/me/password", headers=headers,
                   json={"currentPassword": "bad", "newPassword": "N3w-password!"})
    assert r.status_code == 400 and r.json()["code"] == "INVALID_CURRENT_PASSWORD"
    r = client.put("/api/auth/me/password", headers=headers,
                   json={"currentPassword": PASSWORD, "newPassword": "N3w-password!"})
    assert r.status_code == 204
    assert login(client, "gina@example.com", "N3w-password!").status_code == 200


def test_protected_endpoints_require_valid_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401 and r.json()["code"] == "TOKEN_MISSING"
    assert r.headers["WWW-Authenticate"] == "Bearer"

    forged = jwt.encode({"sub": "x", "iss": "campusconnect-auth", "exp": 9999999999}, "another-secret-of-32-bytes-or-more!!")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401 and r.json()["code"] == "TOKEN_INVALID"

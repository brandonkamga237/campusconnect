from app.config import settings
from tests.conftest import auth_header, make_user


def enroll(client, headers, image: bytes):
    return client.post("/api/auth/me/face", headers=headers, files={"image": ("face.jpg", image, "image/jpeg")})


def face_login(client, email, image: bytes):
    return client.post("/api/auth/login/face", data={"email": email},
                       files={"image": ("face.jpg", image, "image/jpeg")})


def test_enroll_then_login_with_face(client):
    make_user("alice@example.com")
    headers = auth_header(client, "alice@example.com")

    r = enroll(client, headers, b"face:alice")
    assert r.status_code == 201
    assert r.json()["model"] == "fake-128"
    assert "embedding" not in r.json()

    r = face_login(client, "alice@example.com", b"face:alice")
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "alice@example.com"

    me = client.get("/api/auth/me", headers=headers).json()
    assert me["faceEnrolled"] is True and me["faceTemplates"] == 1


def test_face_login_rejects_other_person_and_unknown_accounts(client):
    make_user("alice@example.com")
    enroll(client, auth_header(client, "alice@example.com"), b"face:alice")

    r = face_login(client, "alice@example.com", b"face:mallory")
    assert r.status_code == 401 and r.json()["code"] == "FACE_AUTH_FAILED"

    make_user("bob@example.com")  # pas de visage enregistré
    for email in ("bob@example.com", "ghost@example.com"):
        r = face_login(client, email, b"face:alice")
        assert r.status_code == 401 and r.json()["code"] == "FACE_AUTH_FAILED"


def test_face_mismatches_lock_the_account(client):
    make_user("alice@example.com")
    enroll(client, auth_header(client, "alice@example.com"), b"face:alice")
    for _ in range(settings.max_failed_attempts):
        face_login(client, "alice@example.com", b"face:mallory")
    r = face_login(client, "alice@example.com", b"face:alice")
    assert r.status_code == 423


def test_enroll_validations(client):
    make_user("alice@example.com")
    headers = auth_header(client, "alice@example.com")

    assert client.post("/api/auth/me/face", files={"image": ("f.jpg", b"face:alice")}).status_code == 401

    r = enroll(client, headers, b"noface")
    assert r.status_code == 422 and r.json()["code"] == "NO_FACE_DETECTED"

    assert enroll(client, headers, b"face:alice").status_code == 201
    r = enroll(client, headers, b"face:mallory")  # un autre visage ne peut pas s'ajouter
    assert r.status_code == 422 and r.json()["code"] == "FACE_MISMATCH"

    for _ in range(settings.face_max_templates - 1):
        assert enroll(client, headers, b"face:alice").status_code == 201
    r = enroll(client, headers, b"face:alice")
    assert r.status_code == 409 and r.json()["code"] == "FACE_LIMIT_REACHED"
    assert len(client.get("/api/auth/me/face", headers=headers).json()) == settings.face_max_templates


def test_delete_face_data(client):
    make_user("alice@example.com")
    headers = auth_header(client, "alice@example.com")
    enroll(client, headers, b"face:alice")

    assert client.delete("/api/auth/me/face", headers=headers).status_code == 204
    assert client.get("/api/auth/me/face", headers=headers).json() == []
    assert face_login(client, "alice@example.com", b"face:alice").status_code == 401


def test_face_login_requires_a_face_in_the_image(client):
    r = face_login(client, "alice@example.com", b"noface")
    assert r.status_code == 422 and r.json()["code"] == "NO_FACE_DETECTED"


def test_image_size_limit(client, monkeypatch):
    big = b"x" * (settings.face_max_image_bytes + 1)
    r = face_login(client, "alice@example.com", big)
    assert r.status_code == 413 and r.json()["code"] == "IMAGE_TOO_LARGE"

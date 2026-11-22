"""Tests sans infrastructure : SQLite, pas de config-server/Eureka, moteur de visage factice, emails capturés."""
import hashlib
import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ.update(
    AUTH_SKIP_CONFIG_SERVER="1",
    AUTH_DB_URL=f"sqlite:///{_tmp}/test.db",
    AUTH_REQUIRE_VERIFIED_EMAIL="true",
)

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import face, mailer  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.errors import ApiError  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Role  # noqa: E402
from app.services.auth import create_user  # noqa: E402

PASSWORD = "Sup3r-secret!"


class FakeFaceEngine:
    """Une « image » est un texte : b"face:alice" donne toujours le même vecteur pour alice,
    deux personnes différentes donnent des vecteurs quasi orthogonaux, b"noface" n'a pas de visage."""

    model_name = "fake-128"

    def embed(self, image: bytes) -> np.ndarray:
        if image == b"noface":
            raise ApiError(422, "NO_FACE_DETECTED", "No face was detected in the image")
        seed = int.from_bytes(hashlib.sha256(image).digest()[:8], "big")
        v = np.random.default_rng(seed).standard_normal(128).astype(np.float32)
        return v / np.linalg.norm(v)


@pytest.fixture(autouse=True)
def _db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def fake_face(monkeypatch):
    monkeypatch.setattr(face, "_engine", FakeFaceEngine())


@pytest.fixture
def outbox(monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send_mail", lambda to, subject, body: sent.append((to, subject, body)))
    return sent


@pytest.fixture
def client(outbox):
    with TestClient(create_app(use_lifespan=False)) as c:
        yield c


def token_from(mail_body: str) -> str:
    """Le jeton est sur la ligne qui suit « Ou utilisez ce code »."""
    lines = mail_body.splitlines()
    return lines[lines.index(next(l for l in lines if l.startswith("Ou utilisez ce code"))) + 1].strip()


def make_user(email: str, roles=(Role.STUDENT,), verified=True, password=PASSWORD):
    with SessionLocal() as db:
        user = create_user(db, email, password, set(roles), verified=verified)
        db.commit()
        return user


def login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_header(client, email, password=PASSWORD) -> dict:
    r = login(client, email, password)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['accessToken']}"}

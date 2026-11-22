"""Chargement de la config : valeurs par défaut < config-server < variables d'environnement."""
import json
import logging
import os
import re
import urllib.request
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
log = logging.getLogger("auth-service")

APP_NAME = "auth-service"
CONFIG_SERVER_URL = os.getenv("CONFIG_SERVER_URL", "http://localhost:8888")

DEFAULTS = {
    "server.port": "8081",
    "eureka.client.service-url.defaultZone": "http://localhost:8761/eureka",
    "database.url": "postgresql+psycopg://auth_user:auth@localhost:5432/auth_db",
    "jwt.secret": "dev-secret-change-me-at-least-32-bytes!!",
    "jwt.issuer": "campusconnect-auth",
    "jwt.expiration-minutes": "60",
    "jwt.refresh-expiration-days": "7",
    "auth.max-failed-attempts": "5",
    "auth.lock-minutes": "15",
    "auth.require-verified-email": "true",
    "auth.email-verification-hours": "24",
    "auth.password-reset-minutes": "30",
    "auth.frontend-url": "http://localhost:3000",
    "auth.bootstrap-admin.email": "",
    "auth.bootstrap-admin.password": "",
    "face.model-dir": "models",
    "face.match-threshold": "0.363",
    "face.max-templates": "3",
    "face.max-image-bytes": "5242880",
    "face.encryption-key": "dev-face-key-change-me",
    "mail.host": "localhost",
    "mail.port": "1025",
    "mail.from": "CampusConnect <no-reply@campusconnect.local>",
    "mail.username": "",
    "mail.password": "",
    "mail.starttls": "false",
}

# clé de config -> variable d'environnement qui la surcharge
ENV_OVERRIDES = {
    "server.port": "SERVER_PORT",
    "eureka.client.service-url.defaultZone": "EUREKA_URL",
    "database.url": "AUTH_DB_URL",
    "jwt.secret": "JWT_SECRET",
    "auth.require-verified-email": "AUTH_REQUIRE_VERIFIED_EMAIL",
    "auth.frontend-url": "FRONTEND_URL",
    "auth.bootstrap-admin.email": "ADMIN_EMAIL",
    "auth.bootstrap-admin.password": "ADMIN_PASSWORD",
    "face.model-dir": "FACE_MODEL_DIR",
    "face.encryption-key": "FACE_ENCRYPTION_KEY",
    "mail.host": "MAIL_HOST",
    "mail.port": "MAIL_PORT",
    "mail.from": "MAIL_FROM",
    "mail.username": "MAIL_USERNAME",
    "mail.password": "MAIL_PASSWORD",
    "mail.starttls": "MAIL_STARTTLS",
}

_PLACEHOLDER = re.compile(r"\$\{([^}:]+)(?::([^}]*))?\}")


def _resolve(value: str) -> str:
    """Résout les placeholders Spring ${VAR:default} à partir de l'environnement."""
    return _PLACEHOLDER.sub(lambda m: os.getenv(m.group(1), m.group(2) or ""), value)


def _fetch_config_server() -> dict:
    url = f"{CONFIG_SERVER_URL}/{APP_NAME}/default"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            sources = json.load(resp)["propertySources"]
    except Exception as exc:  # config-server optionnel, comme côté Java
        log.warning("config-server injoignable (%s) : valeurs locales utilisées", exc)
        return {}
    merged = {}
    for source in reversed(sources):  # la première source est la plus prioritaire
        merged.update(source["source"])
    return {k: _resolve(str(v)) for k, v in merged.items()}


def load_raw(fetch_remote: bool = True) -> dict:
    cfg = {**DEFAULTS, **(_fetch_config_server() if fetch_remote else {})}
    for key, env in ENV_OVERRIDES.items():
        if env in os.environ:
            cfg[key] = os.environ[env]
    return cfg


def _bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    port: int
    eureka_url: str
    database_url: str
    jwt_secret: str
    jwt_issuer: str
    access_token_minutes: int
    refresh_token_days: int
    max_failed_attempts: int
    lock_minutes: int
    require_verified_email: bool
    email_verification_hours: int
    password_reset_minutes: int
    frontend_url: str
    bootstrap_admin_email: str
    bootstrap_admin_password: str
    face_model_dir: str
    face_match_threshold: float
    face_max_templates: int
    face_max_image_bytes: int
    face_encryption_key: str
    mail_host: str
    mail_port: int
    mail_from: str
    mail_username: str
    mail_password: str
    mail_starttls: bool

    @classmethod
    def from_raw(cls, c: dict) -> "Settings":
        return cls(
            port=int(c["server.port"]),
            eureka_url=c["eureka.client.service-url.defaultZone"],
            database_url=c["database.url"],
            jwt_secret=c["jwt.secret"],
            jwt_issuer=c["jwt.issuer"],
            access_token_minutes=int(c["jwt.expiration-minutes"]),
            refresh_token_days=int(c["jwt.refresh-expiration-days"]),
            max_failed_attempts=int(c["auth.max-failed-attempts"]),
            lock_minutes=int(c["auth.lock-minutes"]),
            require_verified_email=_bool(c["auth.require-verified-email"]),
            email_verification_hours=int(c["auth.email-verification-hours"]),
            password_reset_minutes=int(c["auth.password-reset-minutes"]),
            frontend_url=c["auth.frontend-url"].rstrip("/"),
            bootstrap_admin_email=c["auth.bootstrap-admin.email"].strip().lower(),
            bootstrap_admin_password=c["auth.bootstrap-admin.password"],
            face_model_dir=c["face.model-dir"],
            face_match_threshold=float(c["face.match-threshold"]),
            face_max_templates=int(c["face.max-templates"]),
            face_max_image_bytes=int(c["face.max-image-bytes"]),
            face_encryption_key=c["face.encryption-key"],
            mail_host=c["mail.host"],
            mail_port=int(c["mail.port"]),
            mail_from=c["mail.from"],
            mail_username=c["mail.username"],
            mail_password=c["mail.password"],
            mail_starttls=_bool(c["mail.starttls"]),
        )


def load(fetch_remote: bool = True) -> Settings:
    return Settings.from_raw(load_raw(fetch_remote))


# Les tests posent AUTH_SKIP_CONFIG_SERVER=1 pour ne pas appeler le config-server.
settings = load(fetch_remote=os.getenv("AUTH_SKIP_CONFIG_SERVER") != "1")

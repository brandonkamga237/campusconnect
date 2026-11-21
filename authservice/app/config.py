"""Chargement de la config : valeurs par défaut < config-server < variables d'environnement."""
import json
import logging
import os
import re
import urllib.request

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("auth-service")

APP_NAME = "auth-service"
CONFIG_SERVER_URL = os.getenv("CONFIG_SERVER_URL", "http://localhost:8888")

DEFAULTS = {
    "server.port": "8081",
    "jwt.secret": "dev-secret-change-me-at-least-32-bytes!!",
    "jwt.expiration-minutes": "60",
    "eureka.client.service-url.defaultZone": "http://localhost:8761/eureka",
}

ENV_OVERRIDES = {
    "server.port": "SERVER_PORT",
    "jwt.secret": "JWT_SECRET",
    "eureka.client.service-url.defaultZone": "EUREKA_URL",
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


def load() -> dict:
    cfg = {**DEFAULTS, **_fetch_config_server()}
    for key, env in ENV_OVERRIDES.items():
        if env in os.environ:
            cfg[key] = os.environ[env]
    return cfg


settings = load()

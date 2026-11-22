"""Enregistrement dans Eureka (discovery-server) pour que la gateway route lb://auth-service."""
import logging
import os
import socket

import py_eureka_client.eureka_client as eureka_client

from app.config import APP_NAME, settings

log = logging.getLogger(APP_NAME)


def instance_host() -> str:
    """IP joignable par les autres services (le hostname d'un conteneur ne l'est pas)."""
    if os.getenv("INSTANCE_HOST"):
        return os.environ["INSTANCE_HOST"]
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("8.8.8.8", 80))  # aucun paquet envoyé, sert à choisir l'interface
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


async def register() -> None:
    host = instance_host()
    try:
        await eureka_client.init_async(
            eureka_server=settings.eureka_url,
            app_name=APP_NAME,
            instance_port=settings.port,
            instance_host=host,
            instance_ip=host,
            health_check_url=f"http://{host}:{settings.port}/actuator/health",
            status_page_url=f"http://{host}:{settings.port}/docs",
        )
    except Exception as exc:
        log.warning("Enregistrement Eureka impossible : %s", exc)


async def unregister() -> None:
    try:
        await eureka_client.stop_async()
    except Exception as exc:
        log.warning("Désinscription Eureka impossible : %s", exc)

import logging
import os
import socket
from contextlib import asynccontextmanager

import py_eureka_client.eureka_client as eureka_client
from fastapi import FastAPI

from app.config import APP_NAME, settings

log = logging.getLogger(APP_NAME)

PORT = int(settings["server.port"])


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


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await eureka_client.init_async(
            eureka_server=settings["eureka.client.service-url.defaultZone"],
            app_name=APP_NAME,
            instance_port=PORT,
            instance_host=instance_host(),
            instance_ip=instance_host(),
            health_check_url="/actuator/health",
        )
    except Exception as exc:
        log.warning("Enregistrement Eureka impossible : %s", exc)
    yield
    await eureka_client.stop_async()


app = FastAPI(title=APP_NAME, lifespan=lifespan)


@app.get("/actuator/health")
def health():
    return {"status": "UP"}


@app.get("/api/auth/ping")
def ping():
    return {"service": APP_NAME, "status": "UP"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import errors, eureka, face
from app.config import APP_NAME, settings
from app.db import SessionLocal
from app.routers import auth, me, users
from app.services.users import bootstrap_admin

log = logging.getLogger(APP_NAME)


@asynccontextmanager
async def lifespan(_: FastAPI):
    face.init_engine()
    try:
        with SessionLocal() as db:
            bootstrap_admin(db)
    except Exception as exc:  # base pas prête : le service démarre quand même, /health le signale
        log.error("Création de l'admin initial impossible : %s", exc)
    await eureka.register()
    yield
    await eureka.unregister()


def create_app(use_lifespan: bool = True) -> FastAPI:
    app = FastAPI(
        title="CampusConnect auth-service",
        version="1.0.0",
        description="Inscription, connexion par email/mot de passe ou reconnaissance faciale, "
        "jetons JWT (HS256) et gestion des rôles.",
        lifespan=lifespan if use_lifespan else None,
    )
    errors.install(app)
    app.include_router(auth.router)
    app.include_router(me.router)
    app.include_router(users.router)

    @app.get("/actuator/health", tags=["Supervision"])
    def health():
        """Utilisé par Eureka et Docker. La reconnaissance faciale est facultative pour être UP."""
        try:
            with SessionLocal() as db:
                db.execute(text("SELECT 1"))
            db_status = "UP"
        except Exception:
            db_status = "DOWN"
        body = {
            "status": db_status,
            "components": {"db": db_status, "face": "UP" if face.engine_ready() else "DOWN"},
        }
        return JSONResponse(body, status_code=200 if db_status == "UP" else 503)

    @app.get("/api/auth/ping", tags=["Supervision"])
    def ping():
        return {"service": APP_NAME, "status": "UP"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.port, proxy_headers=True)

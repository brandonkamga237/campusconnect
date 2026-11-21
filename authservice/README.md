# auth-service

Inscription, connexion par reconnaissance faciale ou empreinte digitale, gestion des rôles (Student, Lecturer, Admin).

| | |
|---|---|
| Langage | Python 3.12 / FastAPI |
| Port | `8081` |
| Santé | `GET http://localhost:8081/actuator/health` |
| Test | `GET http://localhost:8081/api/auth/ping` |
| Doc API | http://localhost:8081/docs |

## Lancer sans Docker

Prérequis : Python 3.12+.

```bash
cd authservice
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

## Lancer avec Docker

```bash
cd authservice
docker build -t campusconnect/auth-service .
docker run --rm -p 8081:8081 campusconnect/auth-service
```

## Configuration

Ordre de priorité : variables d'environnement > config-server (`auth-service.properties`) > valeurs par défaut dans `app/config.py`.

| Variable | Défaut |
|---|---|
| `CONFIG_SERVER_URL` | `http://localhost:8888` |
| `EUREKA_URL` | `http://localhost:8761/eureka` |
| `JWT_SECRET` | `dev-secret-change-me-at-least-32-bytes!!` |
| `SERVER_PORT` | `8081` |
| `INSTANCE_HOST` | IP détectée automatiquement |

config-server et Eureka sont optionnels : le service démarre quand même. S'ils sont démarrés, il charge sa config et s'enregistre dans Eureka sous le nom `auth-service`, ce qui permet à la gateway de le joindre.

`JWT_SECRET` doit être identique à celui de la gateway : elle vérifie les tokens signés (HS256) par ce service.

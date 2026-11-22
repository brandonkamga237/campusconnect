# auth-service

Inscription, connexion par **email/mot de passe** ou **reconnaissance faciale**, jetons JWT et gestion des rôles (STUDENT, LECTURER, ADMIN).

| | |
|---|---|
| Langage | Python 3.12 / FastAPI |
| Port | `8081` |
| Base | PostgreSQL `auth_db` (migrations Alembic) |
| Santé | `GET http://localhost:8081/actuator/health` |
| Doc API (Swagger) | http://localhost:8081/docs |

## Lancer avec Docker (recommandé)

Depuis la racine du projet :

```bash
docker compose up -d --build auth-db mailpit config-server discovery-server api-gateway auth-service
```

Au démarrage, le conteneur applique les migrations, charge les modèles de visage, crée l'admin initial (`admin@campusconnect.dev` / `Admin123!` par défaut) et s'enregistre dans Eureka.

Les emails (vérification, mot de passe oublié) arrivent dans **Mailpit** : http://localhost:8025

## Lancer sans Docker

Prérequis : Python 3.12+, et Postgres + Mailpit démarrés (`docker compose up -d auth-db mailpit`).

```bash
cd authservice
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python scripts/download_models.py        # modèles de visage dans models/ (~38 Mo)
alembic upgrade head                     # crée les tables
MAIL_PORT=1026 ADMIN_EMAIL=admin@campusconnect.dev ADMIN_PASSWORD='Admin123!' python -m app.main
```

Tests (SQLite, sans Postgres ni modèles) : `pytest`

## Endpoints

Tous sous `/api/auth`, joignables via la gateway (`http://localhost:8080/api/auth/...`) ou en direct sur le port 8081.

**Publics**

| Méthode | Chemin | Corps | Réponse |
|---|---|---|---|
| POST | `/register` | `{ email, password }` | `201` utilisateur STUDENT + email de vérification |
| POST | `/verify-email` | `{ token }` | `204` |
| POST | `/verify-email/resend` | `{ email }` | `202` (toujours) |
| POST | `/login` | `{ email, password }` | `200` jetons |
| POST | `/login/face` | multipart : `email`, `image` | `200` jetons |
| POST | `/refresh` | `{ refreshToken }` | `200` nouvelle paire de jetons |
| POST | `/logout` | `{ refreshToken }` | `204` |
| POST | `/password/forgot` | `{ email }` | `202` (toujours) + email |
| POST | `/password/reset` | `{ token, newPassword }` | `204` |

**Utilisateur connecté** (`Authorization: Bearer <accessToken>`)

| Méthode | Chemin | Corps | Réponse |
|---|---|---|---|
| GET | `/me` | | `200` profil + `faceEnrolled` |
| PUT | `/me/password` | `{ currentPassword, newPassword }` | `204` |
| GET | `/me/face` | | `200` échantillons enregistrés |
| POST | `/me/face` | multipart : `image` | `201` (3 maximum) |
| DELETE | `/me/face` | | `204` supprime les données de visage |

**Administration** (rôle ADMIN)

| Méthode | Chemin | Corps | Réponse |
|---|---|---|---|
| GET | `/users?role=&status=&q=&page=&size=` | | `200` page |
| POST | `/users` | `{ email, password, roles[] }` | `201` compte déjà vérifié |
| GET | `/users/{id}` | | `200` |
| PATCH | `/users/{id}` | `{ status?, roles? }` | `200` |

Réponse de connexion :

```json
{ "accessToken": "eyJ...", "refreshToken": "opaque", "tokenType": "Bearer", "expiresIn": 3600,
  "user": { "id": "uuid", "email": "a@b.c", "roles": ["STUDENT"] } }
```

Erreurs au format RFC 9457 (`application/problem+json`) avec un champ `code` stable :

```json
{ "type": "about:blank", "title": "Unauthorized", "status": 401,
  "detail": "Invalid email or password", "instance": "/api/auth/login", "code": "BAD_CREDENTIALS" }
```

| Code HTTP | `code` |
|---|---|
| 400 | `VALIDATION_FAILED` (+ `errors[]`), `TOKEN_INVALID`, `INVALID_CURRENT_PASSWORD` |
| 401 | `BAD_CREDENTIALS`, `FACE_AUTH_FAILED`, `TOKEN_MISSING`, `TOKEN_INVALID`, `TOKEN_EXPIRED`, `TOKEN_REVOKED`, `TOKEN_REUSED` |
| 403 | `EMAIL_NOT_VERIFIED`, `ACCOUNT_DISABLED`, `FORBIDDEN` |
| 404 | `USER_NOT_FOUND` |
| 409 | `EMAIL_TAKEN`, `FACE_LIMIT_REACHED`, `SELF_LOCKOUT` |
| 413 | `IMAGE_TOO_LARGE` |
| 422 | `INVALID_IMAGE`, `NO_FACE_DETECTED`, `MULTIPLE_FACES`, `FACE_MISMATCH` |
| 423 | `ACCOUNT_LOCKED` (+ en-tête `Retry-After`) |
| 503 | `FACE_UNAVAILABLE` (modèles absents) |

## JWT

Signé en HS256 avec `JWT_SECRET`, **le même secret que la gateway**, qui vérifie les tokens sur toutes les routes sauf `/api/auth/**`. Comme la gateway laisse passer `/api/auth/**`, le service vérifie lui-même le token sur `/me` et `/users`.

```json
{ "iss": "campusconnect-auth", "sub": "<userId>", "email": "a@b.c",
  "roles": ["STUDENT"], "iat": 1763700000, "exp": 1763703600, "jti": "<uuid>" }
```

- Access token : 60 min. Refresh token : 7 jours, opaque, stocké haché (SHA-256), **à usage unique**. Réutiliser un refresh token déjà échangé (signe de vol) révoque toutes les sessions de l'utilisateur ; un token révoqué par logout est simplement refusé (`TOKEN_REVOKED`).
- Changer ou réinitialiser le mot de passe, ou désactiver le compte, révoque toutes les sessions.
- 5 échecs de connexion (mot de passe ou visage) verrouillent le compte 15 min.

## Reconnaissance faciale

Modèles pré-entraînés d'[opencv_zoo](https://github.com/opencv/opencv_zoo), exécutés par OpenCV (pas de torch ni tensorflow) :

1. **YuNet** détecte le visage : il en faut exactement un sur la photo.
2. **SFace** calcule un embedding de 128 nombres.
3. La connexion compare l'embedding de la photo à ceux enregistrés **pour cet email** (vérification 1:1) par similarité cosinus. Le seuil de référence de SFace est `0.363`.

Aucune image n'est conservée : seuls les embeddings sont stockés, **chiffrés** avec `FACE_ENCRYPTION_KEY`. Si cette clé change, les visages enregistrés deviennent inutilisables et doivent être réenregistrés.

**Limite connue :** il n'y a pas de détection du vivant. Une photo imprimée ou affichée sur un écran de la bonne personne peut passer. Le mot de passe reste donc la méthode principale ; le visage est un confort.

## Configuration

Priorité : variables d'environnement > config-server (`configurations/auth-service.yml`) > valeurs par défaut de `app/config.py`.

| Variable | Défaut | Rôle |
|---|---|---|
| `AUTH_DB_URL` | `postgresql+psycopg://auth_user:auth@localhost:5432/auth_db` | Base de données |
| `JWT_SECRET` | `dev-secret-change-me-at-least-32-bytes!!` | Identique à la gateway (32 octets minimum) |
| `FACE_ENCRYPTION_KEY` | `dev-face-key-change-me` | Chiffrement des embeddings |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | vides | Admin créé au démarrage s'il n'existe pas |
| `MAIL_HOST` / `MAIL_PORT` | `localhost` / `1025` | SMTP (Mailpit en dev) |
| `MAIL_USERNAME` / `MAIL_PASSWORD` / `MAIL_STARTTLS` | vides / `false` | SMTP réel |
| `FRONTEND_URL` | `http://localhost:3000` | Base des liens envoyés par email |
| `AUTH_REQUIRE_VERIFIED_EMAIL` | `true` | Refuser la connexion tant que l'email n'est pas vérifié |
| `FACE_MODEL_DIR` | `models` | Dossier des modèles ONNX |
| `CONFIG_SERVER_URL` | `http://localhost:8888` | |
| `EUREKA_URL` | `http://localhost:8761/eureka` | |

config-server et Eureka sont optionnels : le service démarre sans eux.

## Structure

```
app/
  main.py          création de l'app, démarrage (modèles, admin, Eureka), /actuator/health
  config.py        chargement de la config
  db.py, models.py SQLAlchemy (tables du schéma USER_DB)
  schemas.py       modèles Pydantic des requêtes/réponses (JSON camelCase)
  security.py      argon2id, JWT, jetons opaques
  face.py          détection + embedding + chiffrement
  mailer.py        emails SMTP
  deps.py          session BD, utilisateur courant, contrôle des rôles
  errors.py        erreurs problem+json
  routers/         endpoints (auth, me, users)
  services/        logique métier
migrations/        Alembic
scripts/           téléchargement des modèles
tests/             pytest
```

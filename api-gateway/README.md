# api-gateway

Point d'entrée unique : routage vers les services et vérification du JWT.

| | |
|---|---|
| Langage | Java 17 / Spring Boot |
| Port | `8080` |
| Santé | `GET http://localhost:8080/actuator/health` |

| Route | Service | JWT requis |
|---|---|---|
| `/api/auth/**` | auth-service | non |
| `/api/attendance/**` | attendance-service | oui |

## Lancer sans Docker

Prérequis : JDK 17+.

```bash
cd api-gateway
./mvnw spring-boot:run
```

## Lancer avec Docker

```bash
cd api-gateway
docker build -t campusconnect/api-gateway .
docker run --rm -p 8080:8080 campusconnect/api-gateway
```

## Dépendances au démarrage

Démarrer avant : `config-server` (routes, port, secret JWT) puis `discovery-server` (résolution `lb://`).
Sans config-server, la gateway démarre mais sans routes.

| Variable | Défaut |
|---|---|
| `CONFIG_SERVER_URL` | `http://localhost:8888` |
| `EUREKA_URL` | `http://localhost:8761/eureka` |
| `JWT_SECRET` | `dev-secret-change-me-at-least-32-bytes!!` |

En Docker seul, la gateway doit joindre les autres conteneurs : préférer le `docker-compose.yml` de la racine.

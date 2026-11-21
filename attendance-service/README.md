# attendance-service

Enregistre et suit les présences aux cours.

| | |
|---|---|
| Langage | Java 17 / Spring Boot |
| Port | `8082` |
| Santé | `GET http://localhost:8082/actuator/health` |
| Test | `GET http://localhost:8082/api/attendance/ping` |

## Lancer sans Docker

Prérequis : JDK 17+.

```bash
cd attendance-service
./mvnw spring-boot:run
```

## Lancer avec Docker

```bash
cd attendance-service
docker build -t campusconnect/attendance-service .
docker run --rm -p 8082:8082 campusconnect/attendance-service
```

## Dépendances au démarrage

Démarrer avant : `config-server` (port) puis `discovery-server` (enregistrement).
Les deux sont optionnels : le service démarre quand même.

| Variable | Défaut |
|---|---|
| `CONFIG_SERVER_URL` | `http://localhost:8888` |
| `EUREKA_URL` | `http://localhost:8761/eureka` |

En Docker seul, préférer le `docker-compose.yml` de la racine pour que le service joigne config-server et Eureka.

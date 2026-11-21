# discovery-server

Annuaire Eureka : enregistre et retrouve les services.

| | |
|---|---|
| Langage | Java 17 / Spring Boot |
| Port | `8761` |
| Santé | `GET http://localhost:8761/actuator/health` |
| Tableau de bord | http://localhost:8761 |

## Lancer sans Docker

Prérequis : JDK 17+.

```bash
cd discovery-server
./mvnw spring-boot:run
```

## Lancer avec Docker

```bash
cd discovery-server
docker build -t campusconnect/discovery-server .
docker run --rm -p 8761:8761 campusconnect/discovery-server
```

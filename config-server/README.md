# config-server

Centralise la configuration de tous les services.

| | |
|---|---|
| Langage | Java 17 / Spring Boot |
| Port | `8888` |
| Santé | `GET http://localhost:8888/actuator/health` |
| Configs servies | `src/main/resources/configurations/<service>.properties` |
| Vérifier | `GET http://localhost:8888/<service>/default` |

## Lancer sans Docker

Prérequis : JDK 17+.

```bash
cd config-server
./mvnw spring-boot:run
```

## Lancer avec Docker

```bash
cd config-server
docker build -t campusconnect/config-server .
docker run --rm -p 8888:8888 campusconnect/config-server
```

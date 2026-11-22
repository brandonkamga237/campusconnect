# student-service

Référentiel académique : facultés, départements, filières, cycles (Licence, Master…), niveaux d'études et cycles proposés par chaque filière.

| | |
|---|---|
| Langage | Java 17 / Spring Boot 4 |
| Port | `8083` |
| Base | PostgreSQL `student_db` (conteneur `student-db`, port hôte `5433`), migrations Flyway |
| Santé | `GET http://localhost:8083/actuator/health` |
| Doc API (Swagger) | http://localhost:8083/swagger-ui.html |

## Lancer

Le plus simple, depuis la racine : `./scripts/start-local.sh` (lance aussi la base et les autres services).

Seul, sans Docker pour le service (JDK 17+) :

```bash
docker compose up -d student-db      # la base
cd student-service
./mvnw spring-boot:run
```

Tests (PostgreSQL lancé automatiquement par Testcontainers, Docker requis) : `./mvnw test`

## Modèle

```
FACULTIES 1───n DEPARTMENTS 1───n FIELDS n───n ACADEMIC_CYCLES 1───n STUDY_LEVELS
                                         (via FIELD_CYCLES)
```

| Table | Contenu |
|---|---|
| `faculties` | code unique, nom, description, statut, dates |
| `departments` | rattaché à une faculté |
| `fields` | filière, rattachée à un département |
| `academic_cycles` | Licence, Master, Doctorat… |
| `study_levels` | niveaux d'un cycle, ordonnés par `position` (unique dans le cycle) |
| `field_cycles` | cycles proposés par une filière, avec un statut |

Les cycles **LICENCE** (L1–L3), **MASTER** (M1–M2) et **DOCTORAT** (D1–D3) sont créés par la migration `V2__lmd_reference_data.sql` ; ils restent modifiables via l'API.

Règles :

- Les codes sont uniques et stockés en majuscules (`gl` devient `GL`).
- Statut `ACTIVE` ou `INACTIVE`. On ne peut pas rattacher un élément à un parent `INACTIVE` (`409 PARENT_INACTIVE`).
- Un élément qui a encore des enfants ne peut pas être supprimé (`409 RESOURCE_IN_USE`) : supprimer les enfants ou le passer `INACTIVE`. Supprimer une filière supprime ses cycles rattachés.

## Sécurité

JWT émis par auth-service (HS256, même `JWT_SECRET`, émetteur `campusconnect-auth`), vérifié par la gateway **et** par le service.

- `GET` : tout utilisateur connecté (STUDENT, LECTURER, ADMIN).
- `POST`, `PUT`, `PATCH`, `DELETE` : rôle **ADMIN**.

## Endpoints

Via la gateway (`http://localhost:8080`) ou en direct (`http://localhost:8083`).

| Méthode | Chemin | Corps / paramètres |
|---|---|---|
| GET | `/api/faculties` | `?status=&q=&page=&size=&sort=name,asc` → page |
| GET | `/api/faculties/{id}` | |
| POST | `/api/faculties` | `{ code, name, description? }` → `201` |
| PUT | `/api/faculties/{id}` | `{ code, name, description? }` |
| PATCH | `/api/faculties/{id}/status` | `{ status }` |
| DELETE | `/api/faculties/{id}` | `204` |
| GET | `/api/departments` | `?facultyId=&status=&q=&page=&size=&sort=` → page |
| GET / PUT / PATCH `…/status` / DELETE | `/api/departments/{id}` | corps : `{ facultyId, code, name, description? }` |
| POST | `/api/departments` | `{ facultyId, code, name, description? }` → `201` |
| GET | `/api/fields` | `?departmentId=&facultyId=&status=&q=&page=&size=&sort=` → page |
| GET / PUT / PATCH `…/status` / DELETE | `/api/fields/{id}` | corps : `{ departmentId, code, name, description? }` |
| POST | `/api/fields` | `{ departmentId, code, name, description? }` → `201` |
| GET | `/api/fields/{id}/cycles` | cycles proposés par la filière |
| POST | `/api/fields/{id}/cycles` | `{ academicCycleId }` → `201` |
| PATCH | `/api/fields/{id}/cycles/{academicCycleId}/status` | `{ status }` |
| DELETE | `/api/fields/{id}/cycles/{academicCycleId}` | `204` |
| GET | `/api/academic-cycles` | `?status=` → liste |
| GET | `/api/academic-cycles/{id}/levels` | niveaux du cycle, par position |
| GET / PUT / PATCH `…/status` / DELETE | `/api/academic-cycles/{id}` | corps : `{ code, name, description? }` |
| POST | `/api/academic-cycles` | `{ code, name, description? }` → `201` |
| GET | `/api/study-levels` | `?academicCycleId=` → liste |
| GET / PUT / DELETE | `/api/study-levels/{id}` | corps : `{ academicCycleId, code, name, position }` |
| POST | `/api/study-levels` | `{ academicCycleId, code, name, position }` → `201` |

Exemple de réponse (filière) :

```json
{ "id": "uuid", "code": "GL", "name": "Génie logiciel", "description": null, "status": "ACTIVE",
  "department": { "id": "uuid", "code": "INFO", "name": "Informatique" },
  "faculty": { "id": "uuid", "code": "FST", "name": "Faculté des sciences et techniques" },
  "createdAt": "2026-11-22T11:00:00Z", "updatedAt": "2026-11-22T11:00:00Z" }
```

Pages : `{ "content": [...], "page": { "size": 20, "number": 0, "totalElements": 1, "totalPages": 1 } }` (taille 20 par défaut, 100 maximum).

Erreurs au format RFC 9457 (`application/problem+json`) avec un champ `code` :

| Code HTTP | `code` |
|---|---|
| 400 | `VALIDATION_FAILED` (+ `errors[]`), `INVALID_PARAMETER`, `INVALID_SORT` |
| 401 | `TOKEN_MISSING`, `TOKEN_INVALID` |
| 403 | `FORBIDDEN` |
| 404 | `FACULTY_NOT_FOUND`, `DEPARTMENT_NOT_FOUND`, `FIELD_NOT_FOUND`, `ACADEMIC_CYCLE_NOT_FOUND`, `STUDY_LEVEL_NOT_FOUND`, `FIELD_CYCLE_NOT_FOUND` |
| 409 | `CODE_TAKEN`, `POSITION_TAKEN`, `FIELD_CYCLE_EXISTS`, `PARENT_INACTIVE`, `RESOURCE_IN_USE` |

## Configuration

Priorité : variables d'environnement > config-server (`configurations/student-service.yml`) > `src/main/resources/application.yml`.

| Variable | Défaut |
|---|---|
| `STUDENT_DB_URL` | `jdbc:postgresql://localhost:5433/student_db` |
| `STUDENT_DB_USER` / `STUDENT_DB_PASSWORD` | `student_user` / `student` |
| `JWT_SECRET` | `dev-secret-change-me-at-least-32-bytes!!` (identique à auth-service et à la gateway) |
| `CONFIG_SERVER_URL` | `http://localhost:8888` |
| `EUREKA_URL` | `http://localhost:8761/eureka` |

## Structure

```
src/main/java/com/groupetp1/student_service/
  academic/   entités, dépôts, services (règles métier), contrôleurs, DTO
  common/     statut, erreurs problem+json, filtres de recherche, classes de base
  config/     sécurité JWT, pagination
src/main/resources/db/migration/   migrations Flyway
src/test/                          tests d'intégration (MockMvc + Testcontainers)
```

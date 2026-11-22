# CampusConnect

Projet de TP en microservices.

## Cloner le projet

```bash
git clone git@github.com:brandonkamga237/campusconnect.git
cd campusconnect
git config core.hooksPath .githooks   # active le hook qui refuse les "Co-authored-by"
```

## Lancer en local (développement)

Prérequis : Docker, JDK 17+, Python 3.12+.

```bash
./scripts/start-local.sh   # Ctrl+C arrête tout
```

Seules les bases (`auth-db`, `student-db`) et Mailpit tournent dans Docker. Les services Java se lancent avec `./mvnw spring-boot:run` et auth-service avec Python, dans l'ordre : config-server, discovery-server, auth-service, student-service, api-gateway. Le script attend que chaque service soit prêt avant de lancer le suivant ; les logs sont dans `.logs/`.

## Documentation des API et tests Postman

| Service | Swagger |
|---|---|
| auth-service | http://localhost:8081/docs |
| student-service | http://localhost:8083/swagger-ui.html |

Dans Swagger, obtenir un jeton avec `POST /api/auth/login` (sur auth-service), puis le coller via le bouton « Authorize ».

Collection Postman : [`CampusConnect.postman_collection.json`](CampusConnect.postman_collection.json), à importer dans Postman (Import > fichier). Elle passe par la gateway (`http://localhost:8080`) et se joue dans l'ordre des dossiers, par exemple avec « Run collection » :

- les jetons et identifiants créés sont enregistrés automatiquement dans les variables de la collection ;
- les jetons envoyés par email (vérification, mot de passe oublié) sont lus automatiquement dans Mailpit ;
- le dossier « 2 · Auth – reconnaissance faciale » demande de choisir une photo pour le champ `image` de chaque requête (le décocher pour une exécution sans photo) ;
- le dernier dossier supprime tout ce que la collection a créé.

## Lancer avec Docker Compose

Prérequis : Docker et Docker Compose.

```bash
docker compose up -d --build   # build + démarrage
docker compose ps              # état des conteneurs
docker compose logs -f <service>
docker compose down            # arrêt
```

Services disponibles dans le compose :

| Service | Dossier | Langage | Port |
|---|---|---|---|
| `config-server` | `config-server/` | Java | 8888 |
| `discovery-server` | `discovery-server/` | Java | 8761 |
| `api-gateway` | `api-gateway/` | Java | 8080 |
| `auth-service` | `authservice/` | Python | 8081 |
| `student-service` | `student-service/` | Java | 8083 |
| `auth-db` | — | PostgreSQL 17 (base de auth-service) | 5432 |
| `student-db` | — | PostgreSQL 17 (base de student-service) | 5433 |
| `mailpit` | — | SMTP de dev | 8025 (interface web), 1026 (SMTP) |

`config-server` et `discovery-server` démarrent en premier ; les autres attendent qu'ils soient prêts.

Chaque service a son propre conteneur PostgreSQL (`auth-db` pour auth-service, `student-db` pour student-service). La base et l'utilisateur sont créés au premier démarrage à partir des variables `POSTGRES_*` du compose ; `docker compose down -v` repart de zéro (et efface les données).

Tous les emails envoyés par les services (vérification, mot de passe oublié) sont capturés par Mailpit : http://localhost:8025

Compte administrateur créé au premier démarrage : `admin@campusconnect.dev` / `Admin123!` (variables `ADMIN_EMAIL` / `ADMIN_PASSWORD`).

Vérifier que tout tourne :

| Test | Résultat attendu |
|---|---|
| http://localhost:8761 | `API-GATEWAY`, `AUTH-SERVICE`, `STUDENT-SERVICE` listés |
| `curl localhost:8080/api/auth/ping` | `{"service":"auth-service","status":"UP"}` (via la gateway) |
| `curl -i localhost:8080/api/auth/me` | `401` : JWT requis |
| `curl -i localhost:8080/api/faculties` | `401` : JWT requis par la gateway |

Le secret JWT se change avec la variable `JWT_SECRET` (fichier `.env` à la racine ou export avant `docker compose up`).

Pour lancer un service seul, avec ou sans Docker : voir le `README.md` de son dossier.

## Services de base

| Service | Rôle |
|---|---|
| `config-server` | Centralise la configuration de tous les services |
| `discovery-server` | Annuaire : enregistre et retrouve les services |
| `api-gateway` | Point d'entrée unique, routage, vérification du JWT |

## Services métier

| Service | Rôle |
|---|---|
| `auth-service` | Inscription, connexion par email/mot de passe ou reconnaissance faciale, gestion des rôles (Student, Lecturer, Admin) |
| `student-service` | Référentiel académique : facultés, départements, filières, cycles et niveaux d'études |
| `course-service` | Créer un cours, assigner un enseignant, lister les cours, suivre les performances par cours |
| `enrollment-service` | Inscrire un étudiant à un cours, vérifier la capacité |
| `payment-service` | Payer les frais de scolarité, consulter le statut du paiement |
| `notification-service` | Envoyer un email, un SMS ou un WhatsApp après une inscription ou un paiement |
| `grade-service` | Saisir et consulter les notes des étudiants |
| `attendance-service` | Enregistrer et suivre les présences aux cours |
| `timetable-service` | Gérer les emplois du temps |
| `reporting-service` | Produire des rapports et des statistiques |

# CampusConnect

Projet de TP en microservices.

## Cloner le projet

```bash
git clone git@github.com:brandonkamga237/campusconnect.git
cd campusconnect
git config core.hooksPath .githooks   # active le hook qui refuse les "Co-authored-by"
```

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
| `attendance-service` | `attendance-service/` | Java | 8082 |

`config-server` et `discovery-server` démarrent en premier ; les autres attendent qu'ils soient prêts.

Vérifier que tout tourne :

| Test | Résultat attendu |
|---|---|
| http://localhost:8761 | `API-GATEWAY`, `AUTH-SERVICE`, `ATTENDANCE-SERVICE` listés |
| `curl localhost:8080/api/auth/ping` | `{"service":"auth-service","status":"UP"}` (via la gateway) |
| `curl -i localhost:8080/api/attendance/ping` | `401` : JWT requis par la gateway |
| `curl localhost:8082/api/attendance/ping` | `{"service":"attendance-service","status":"UP"}` (en direct) |

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
| `auth-service` | Inscription, connexion par reconnaissance faciale ou empreinte digitale, gestion des rôles (Student, Lecturer, Admin) |
| `student-service` | Créer, modifier et lister les profils étudiants |
| `course-service` | Créer un cours, assigner un enseignant, lister les cours, suivre les performances par cours |
| `enrollment-service` | Inscrire un étudiant à un cours, vérifier la capacité |
| `payment-service` | Payer les frais de scolarité, consulter le statut du paiement |
| `notification-service` | Envoyer un email, un SMS ou un WhatsApp après une inscription ou un paiement |
| `grade-service` | Saisir et consulter les notes des étudiants |
| `attendance-service` | Enregistrer et suivre les présences aux cours |
| `timetable-service` | Gérer les emplois du temps |
| `reporting-service` | Produire des rapports et des statistiques |

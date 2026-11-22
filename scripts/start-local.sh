#!/usr/bin/env bash
# Lance CampusConnect en local, sans conteneuriser les microservices :
#   - Docker uniquement pour l'infrastructure : auth-db, student-db (PostgreSQL) et mailpit (SMTP de dev)
#   - services Java avec ./mvnw spring-boot:run, auth-service avec Python (venv)
#
# Usage : ./scripts/start-local.sh        (Ctrl+C arrête tout)
# Logs  : .logs/<service>.log
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGS="$ROOT/.logs"
mkdir -p "$LOGS"
cd "$ROOT"

# Variables partagées (JWT_SECRET, mots de passe…) : fichier .env à la racine s'il existe.
if [ -f .env ]; then set -a; . ./.env; set +a; fi

INFRA=(auth-db student-db mailpit)
PIDS=()

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*" >&2; }
step()  { printf '\033[1m==> %s\033[0m\n' "$*"; }

cleanup() {
  trap - INT TERM EXIT
  echo
  step "Arrêt des services"
  for pid in "${PIDS[@]}"; do
    kill -- "-$pid" 2>/dev/null || true   # tout le groupe : mvnw + JVM, ou python
  done
  wait 2>/dev/null || true
  docker compose stop "${INFRA[@]}" >/dev/null 2>&1 || true
  green "Tout est arrêté."
}
trap cleanup INT TERM EXIT

require() {
  command -v "$1" >/dev/null || { red "Commande introuvable : $1"; exit 1; }
}

check_port_free() {
  if ss -ltn | awk '{print $4}' | grep -qE "[:.]$1\$"; then
    red "Le port $1 est déjà utilisé ($2). Libérez-le puis relancez."
    exit 1
  fi
}

# wait_http <nom> <url> <timeout-secondes> <pid>
wait_http() {
  local name=$1 url=$2 timeout=$3 pid=$4 waited=0
  until curl -fs -o /dev/null "$url"; do
    if ! kill -0 "$pid" 2>/dev/null; then
      red "$name s'est arrêté au démarrage. Fin du log :"
      tail -n 30 "$LOGS/$name.log" >&2
      exit 1
    fi
    if [ "$waited" -ge "$timeout" ]; then
      red "$name n'a pas répondu sur $url après ${timeout}s (log : .logs/$name.log)"
      exit 1
    fi
    sleep 2; waited=$((waited + 2))
  done
  green "    $name prêt ($url)"
}

# start <nom> <dossier> <commande...> : lance en arrière-plan dans son propre groupe de processus
start() {
  local name=$1 dir=$2; shift 2
  (cd "$dir" && exec setsid "$@") >"$LOGS/$name.log" 2>&1 &
  PIDS+=("$!")
  LAST_PID=$!
}

start_java() {
  local name=$1 port=$2
  check_port_free "$port" "$name"
  step "$name (port $port)"
  start "$name" "$ROOT/$name" ./mvnw -q spring-boot:run
  wait_http "$name" "http://localhost:$port/actuator/health" 240 "$LAST_PID"
}

# --- prérequis -------------------------------------------------------------------------------
for cmd in docker curl java python3 setsid ss; do require "$cmd"; done
for p in 8888:config-server 8761:discovery-server 8081:auth-service 8083:student-service 8080:api-gateway; do
  check_port_free "${p%%:*}" "${p#*:}"
done

# --- infrastructure (Docker) -----------------------------------------------------------------
step "Infrastructure Docker : ${INFRA[*]}"
docker compose up -d --wait "${INFRA[@]}"
green "    auth-db : localhost:5432 · student-db : localhost:5433 · mailpit : http://localhost:8025 (SMTP localhost:1026)"

# --- services de base ------------------------------------------------------------------------
start_java config-server 8888
start_java discovery-server 8761

# --- auth-service (Python) -------------------------------------------------------------------
step "auth-service (port 8081)"
AUTH_DIR="$ROOT/authservice"
if [ ! -x "$AUTH_DIR/.venv/bin/python" ]; then
  echo "    création du venv et installation des dépendances…"
  python3 -m venv "$AUTH_DIR/.venv"
  "$AUTH_DIR/.venv/bin/pip" install -q -r "$AUTH_DIR/requirements.txt"
fi
(cd "$AUTH_DIR" && .venv/bin/python scripts/download_models.py models >/dev/null)

export AUTH_DB_URL="postgresql+psycopg://auth_user:${AUTH_DB_PASSWORD:-auth}@localhost:5432/auth_db"
export MAIL_HOST=localhost MAIL_PORT=1026
export FACE_MODEL_DIR=models INSTANCE_HOST=127.0.0.1
export ADMIN_EMAIL="${ADMIN_EMAIL:-admin@campusconnect.dev}" ADMIN_PASSWORD="${ADMIN_PASSWORD:-Admin123!}"

(cd "$AUTH_DIR" && .venv/bin/alembic upgrade head) >"$LOGS/auth-service-migrations.log" 2>&1 \
  || { red "Migrations échouées :"; tail -n 20 "$LOGS/auth-service-migrations.log" >&2; exit 1; }
start auth-service "$AUTH_DIR" .venv/bin/python -m app.main
wait_http auth-service "http://localhost:8081/actuator/health" 120 "$LAST_PID"

# --- student-service (Java) -----------------------------------------------------------------
start_java student-service 8083

# --- point d'entrée --------------------------------------------------------------------------
start_java api-gateway 8080

echo
green "CampusConnect tourne en local :"
cat <<EOF
    Gateway        http://localhost:8080   (ex. curl localhost:8080/api/auth/ping)
    Eureka         http://localhost:8761
    Config         http://localhost:8888/auth-service/default
    Auth (Swagger) http://localhost:8081/docs
    Student        http://localhost:8083   (ex. GET /api/academic-cycles avec un JWT)
    Mailpit        http://localhost:8025
    Admin          ${ADMIN_EMAIL} / ${ADMIN_PASSWORD}
    Logs           .logs/
Ctrl+C pour tout arrêter.
EOF

wait

#!/usr/bin/env bash
# Deploy a pre-built Spring Boot API JAR with backup, restart, health check, and rollback.
# Intended to be installed as /usr/local/sbin/watermark-api-deploy and invoked via sudo
# by the unprivileged GitHub Actions deploy user.
set -euo pipefail

REMOTE_JAR="${1:-}"
GIT_SHA="${2:-unknown}"
HEALTH_URL="${3:-https://api.loadsadar.asia/actuator/health}"

APP_JAR=/opt/watermark-api/app.jar
BACKUP_DIR=/opt/watermark-api/backups
SERVICE=watermark-api
OWNER=www-data
GROUP=www-data

log() {
  printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"
}

fail() {
  log "ERROR: $*" >&2
  exit 1
}

[[ $EUID -eq 0 ]] || fail "must run as root"
[[ -n "$REMOTE_JAR" ]] || fail "missing remote jar argument"
[[ -f "$REMOTE_JAR" ]] || fail "uploaded jar not found: $REMOTE_JAR"
[[ "$REMOTE_JAR" == /tmp/watermark-api-*.jar ]] || fail "refusing unexpected jar path: $REMOTE_JAR"

SHORT_SHA="${GIT_SHA:0:12}"
TS="$(date -u +%Y%m%d%H%M%S)"
BACKUP_JAR="${BACKUP_DIR}/app-${TS}-${SHORT_SHA}.jar"

cleanup() {
  rm -f "$REMOTE_JAR"
}
trap cleanup EXIT

mkdir -p "$BACKUP_DIR"

if [[ -f "$APP_JAR" ]]; then
  cp "$APP_JAR" "$BACKUP_JAR"
  log "backed up current jar to $BACKUP_JAR"
else
  log "no existing app.jar found; rollback is unavailable for this first deploy"
  BACKUP_JAR=""
fi

rollback() {
  local status=$?
  if [[ -n "${BACKUP_JAR}" && -f "${BACKUP_JAR}" ]]; then
    log "deployment failed; rolling back to $BACKUP_JAR"
    install -m 0644 -o "$OWNER" -g "$GROUP" "$BACKUP_JAR" "$APP_JAR"
    systemctl restart "$SERVICE"
    sleep 5
    systemctl is-active --quiet "$SERVICE" || true
  else
    log "deployment failed and no backup jar is available"
  fi
  exit "$status"
}
trap rollback ERR

install -m 0644 -o "$OWNER" -g "$GROUP" "$REMOTE_JAR" "$APP_JAR"
log "installed new jar for $SHORT_SHA"

systemctl restart "$SERVICE"
log "restarted $SERVICE"

for _ in {1..30}; do
  if systemctl is-active --quiet "$SERVICE" && curl -fsS "$HEALTH_URL" | grep -q '"status":"UP"'; then
    log "$SERVICE is healthy after deploy: $SHORT_SHA"
    trap - ERR
    exit 0
  fi
  sleep 2
done

log "$SERVICE did not become healthy in time"
journalctl -u "$SERVICE" -n 80 --no-pager || true
false

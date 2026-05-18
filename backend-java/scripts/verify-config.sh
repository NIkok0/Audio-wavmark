#!/usr/bin/env bash
# 一键校验部署相关配置与连通性（Linux / Git Bash / macOS）。
# 请在 backend-java 目录下执行（或写全路径）。若在仓库根 watermarking/ 下：
#   chmod +x backend-java/scripts/verify-config.sh
#   ./backend-java/scripts/verify-config.sh --env-file ...
#
# 用法示例（当前目录为 backend-java）：
#   chmod +x scripts/verify-config.sh
#   # 仅校验当前 shell 已 export 的 WM_* / Spring 相关变量 + TCP
#   ./scripts/verify-config.sh
#
#   # 先加载服务器上的 env 文件再校验（勿将含密钥的文件提交 Git）
#   ./scripts/verify-config.sh --env-file /opt/watermark-api/watermark-api.env
#
#   # 再检查公网 API 健康（可选）
#   ./scripts/verify-config.sh --env-file ./deploy/watermark-api.env.example --api-url https://api.loadsadar.asia
#
# Windows（无 Bash，在 backend-java 下）：powershell -File scripts/verify-config.ps1 -EnvFile .\deploy\watermark-api.env.example -Strict
# 若在仓库根：powershell -File backend-java/scripts/verify-config.ps1 ...
#
#   # 严格模式：缺任一关键变量则失败退出
#   ./scripts/verify-config.sh --env-file /path/to/env --strict
#
set -u

RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0
STRICT=0
ENV_FILE=""
API_URL=""

usage() {
  sed -n '1,30p' "${BASH_SOURCE[0]}" | tail -n +2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE=${2:-}
      shift 2 || usage
      ;;
    --api-url)
      API_URL=${2:-}
      shift 2 || usage
      ;;
    --strict)
      STRICT=1
      shift
      ;;
    -h|--help) usage ;;
    *) echo "未知参数: $1" >&2; usage ;;
  esac
done

ok() { echo -e "${GRN}[OK]${NC} $*"; }
warn() { echo -e "${YLW}[WARN]${NC} $*"; WARNINGS=$((WARNINGS + 1)); }
fail() { echo -e "${RED}[FAIL]${NC} $*"; ERRORS=$((ERRORS + 1)); }

if [[ -n "$ENV_FILE" ]]; then
  if [[ ! -f "$ENV_FILE" ]]; then
    fail "环境文件不存在: $ENV_FILE"
    exit 1
  fi
  # shellcheck source=/dev/null
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  ok "已加载环境文件: $ENV_FILE"
fi

check_nonempty() {
  local name=$1
  local val=${2:-}
  if [[ -z "$val" ]]; then
    if [[ "$STRICT" -eq 1 ]]; then
      fail "缺少或未设置: $name"
    else
      warn "未设置（可选或待填）: $name"
    fi
  else
    ok "已设置: $name"
  fi
}

# 生产/联调常用变量（与 deploy/watermark-api.env.example 对齐）
check_nonempty "WM_PROFILE" "${WM_PROFILE:-}"
check_nonempty "WM_DATASOURCE_URL" "${WM_DATASOURCE_URL:-}"
check_nonempty "WM_DATASOURCE_USERNAME" "${WM_DATASOURCE_USERNAME:-}"
check_nonempty "WM_DATASOURCE_PASSWORD" "${WM_DATASOURCE_PASSWORD:-}"
check_nonempty "WM_REDIS_HOST" "${WM_REDIS_HOST:-localhost}"
check_nonempty "WM_REDIS_PORT" "${WM_REDIS_PORT:-6379}"
check_nonempty "WM_INSTANCE_PATH" "${WM_INSTANCE_PATH:-}"

if [[ -n "${WM_STORAGE_BACKEND:-}" ]]; then
  ok "WM_STORAGE_BACKEND=${WM_STORAGE_BACKEND}"
  if [[ "${WM_STORAGE_BACKEND,,}" == "minio" ]]; then
    check_nonempty "WM_MINIO_ENDPOINT" "${WM_MINIO_ENDPOINT:-}"
  elif [[ "${WM_STORAGE_BACKEND,,}" == "cos" ]]; then
    check_nonempty "WM_COS_SECRET_ID" "${WM_COS_SECRET_ID:-}"
    check_nonempty "WM_COS_SECRET_KEY" "${WM_COS_SECRET_KEY:-}"
    check_nonempty "WM_COS_BUCKET" "${WM_COS_BUCKET:-}"
  fi
else
  warn "未设置 WM_STORAGE_BACKEND（默认由 application.yml 处理）"
fi

# CORS（跨子域时建议开启）
WM_CORS_ENABLED_LC=$(printf '%s' "${WM_CORS_ENABLED:-false}" | tr '[:upper:]' '[:lower:]')
if [[ "$WM_CORS_ENABLED_LC" == "true" ]]; then
  check_nonempty "WM_CORS_ALLOWED_ORIGINS" "${WM_CORS_ALLOWED_ORIGINS:-}"
fi

# 从 JDBC URL 解析 MySQL 主机与端口
MYSQL_HOST=""
MYSQL_PORT="3306"
if [[ -n "${WM_DATASOURCE_URL:-}" ]]; then
  if [[ "${WM_DATASOURCE_URL}" =~ jdbc:mysql://([^/:?]+)(:([0-9]+))?/ ]]; then
    MYSQL_HOST="${BASH_REMATCH[1]}"
    if [[ -n "${BASH_REMATCH[3]:-}" ]]; then
      MYSQL_PORT="${BASH_REMATCH[3]}"
    fi
  else
    warn "无法从 WM_DATASOURCE_URL 解析主机（请确认 jdbc:mysql://host:port/ 格式）"
  fi
fi

tcp_check() {
  local host=$1
  local port=$2
  local label=$3
  if [[ -z "$host" || -z "$port" ]]; then
    warn "跳过 TCP: $label（主机或端口为空）"
    return
  fi
  if command -v nc >/dev/null 2>&1; then
    if nc -z -w3 "$host" "$port" 2>/dev/null \
      || nc -G 3 -z "$host" "$port" 2>/dev/null \
      || nc -z "$host" "$port" 2>/dev/null; then
      ok "TCP 可达: $label ($host:$port)"
    else
      fail "TCP 不可达: $label ($host:$port)"
    fi
  elif timeout 2 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
    ok "TCP 可达: $label ($host:$port)"
  else
    warn "未安装 nc 且 /dev/tcp 不可用，跳过 TCP: $label ($host:$port)"
  fi
}

if [[ -n "$MYSQL_HOST" ]]; then
  tcp_check "$MYSQL_HOST" "$MYSQL_PORT" "MySQL"
fi

REDIS_HOST="${WM_REDIS_HOST:-localhost}"
REDIS_PORT="${WM_REDIS_PORT:-6379}"
tcp_check "$REDIS_HOST" "$REDIS_PORT" "Redis"

WM_SB_LC=$(printf '%s' "${WM_STORAGE_BACKEND:-minio}" | tr '[:upper:]' '[:lower:]')
if [[ -n "${WM_MINIO_ENDPOINT:-}" ]] && [[ "$WM_SB_LC" != "cos" ]]; then
  # 简单解析 http://host:9000
  me="${WM_MINIO_ENDPOINT}"
  me="${me#http://}"
  me="${me#https://}"
  mh="${me%%:*}"
  mp="${me#*:}"
  mp="${mp%%/*}"
  if [[ -n "$mh" && -n "$mp" && "$mh" != "$me" ]]; then
    tcp_check "$mh" "$mp" "MinIO(WM_MINIO_ENDPOINT)"
  else
    warn "无法从 WM_MINIO_ENDPOINT 解析 host:port: $WM_MINIO_ENDPOINT"
  fi
fi

if command -v redis-cli >/dev/null 2>&1; then
  if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ${WM_REDIS_PASSWORD:+-a "$WM_REDIS_PASSWORD"} ping 2>/dev/null | grep -q PONG; then
    ok "Redis PING 成功 ($REDIS_HOST:$REDIS_PORT)"
  else
    fail "Redis PING 失败 ($REDIS_HOST:$REDIS_PORT)（若需密码请设置 WM_REDIS_PASSWORD）"
  fi
else
  warn "未安装 redis-cli，跳过 Redis PING"
fi

if [[ -n "$API_URL" ]]; then
  base="${API_URL%/}"
  if command -v curl >/dev/null 2>&1; then
    HEALTH_TMP=$(mktemp 2>/dev/null || echo "/tmp/wm-health-$$.json")
    trap 'rm -f "$HEALTH_TMP" 2>/dev/null' EXIT
    code=$(curl -sS -o "$HEALTH_TMP" -w "%{http_code}" "$base/actuator/health" || true)
    if [[ "$code" == "200" ]]; then
      ok "HTTP $code: $base/actuator/health"
      if grep -q '"status":"UP"' "$HEALTH_TMP" 2>/dev/null; then
        ok "健康内容包含 status=UP"
      else
        warn "响应 200 但未发现标准 UP 字段，请人工查看: $HEALTH_TMP"
      fi
    else
      fail "HTTP $code: $base/actuator/health"
    fi
  else
    fail "未安装 curl，无法检查 --api-url"
  fi
fi

echo ""
if [[ "$ERRORS" -eq 0 ]]; then
  echo -e "${GRN}校验结束：无阻塞错误${NC}（警告数: $WARNINGS）"
  exit 0
else
  echo -e "${RED}校验结束：存在 $ERRORS 个错误${NC}（警告数: $WARNINGS）"
  exit 1
fi

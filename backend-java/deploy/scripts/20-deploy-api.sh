#!/usr/bin/env bash
# 20-deploy-api.sh
# 部署 Spring Boot API：拷 jar、生成 env 文件、装 systemd、启动。
# 幂等：可多次执行（会覆盖 /opt/watermark-api/app.jar 和 systemd unit）。
#
# 使用：
#   sudo bash 20-deploy-api.sh /path/to/web-0.1.0-SNAPSHOT.jar
#
# 前置：
#   1) 已跑过 00-install-server.sh 和 10-init-mysql.sh
#   2) 已把 cos 桶、SecretId/Key 准备好（第一次跑会 read -s 询问）
#   3) 已把本机产物用 scp 传到 CVM（例如 /tmp/app.jar）

set -euo pipefail
log() { printf "\n[\e[32m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
warn() { printf "\n[\e[33m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
fail() { printf "\n[\e[31m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "必须以 root 运行：sudo bash $0 /path/to/app.jar"

JAR_SRC="${1:-}"
[[ -n "$JAR_SRC" && -f "$JAR_SRC" ]] || fail "请传入 Jar 路径：sudo bash $0 /path/to/app.jar"

# 加载已写好的 MySQL 凭据
[[ -f /etc/watermark/db.env ]] || fail "未找到 /etc/watermark/db.env，请先执行 10-init-mysql.sh"
# shellcheck disable=SC1091
set -a; source /etc/watermark/db.env; set +a

API_DIR=/opt/watermark-api
ENV_FILE=$API_DIR/watermark-api.env
DATA_DIR=/opt/watermark-data/instance

log "1/5 拷贝 Jar 到 ${API_DIR}/app.jar"
install -m 0644 -o www-data -g www-data "$JAR_SRC" "$API_DIR/app.jar"

# ---- 第二次以后可以跳过询问：如果 env 文件里已有 cos 关键字段，就复用 ----
need_cos_input=1
if [[ -s "$ENV_FILE" ]] && grep -q '^WM_COS_SECRET_ID=' "$ENV_FILE" && grep -q '^WM_COS_SECRET_KEY=' "$ENV_FILE"; then
  need_cos_input=0
  log "检测到 $ENV_FILE 已包含 COS 凭据，跳过交互"
fi

if [[ "$need_cos_input" == "1" ]]; then
  log "2/5 收集 COS 配置"
  read -rp "COS 桶名（例如 watermark-1300000000）: " WM_COS_BUCKET
  read -rp "COS 地域（默认 ap-guangzhou）: " WM_COS_REGION
  WM_COS_REGION=${WM_COS_REGION:-ap-guangzhou}
  read -rp "COS SecretId: " WM_COS_SECRET_ID
  read -rsp "COS SecretKey（不会回显）: " WM_COS_SECRET_KEY; echo
  [[ -n "$WM_COS_BUCKET" && -n "$WM_COS_SECRET_ID" && -n "$WM_COS_SECRET_KEY" ]] || fail "COS 三项不能为空"

  log "是否现在启用首个管理员 bootstrap？（y/N，仅空库首次部署建议 y）"
  read -rp "> " bootstrap_yn
  bootstrap_yn=${bootstrap_yn:-n}
  if [[ "$bootstrap_yn" =~ ^[yY]$ ]]; then
    read -rp "管理员用户名（默认 admin）: " BOOT_USER; BOOT_USER=${BOOT_USER:-admin}
    read -rp "管理员邮箱（默认 admin@loadsadar.asia）: " BOOT_EMAIL; BOOT_EMAIL=${BOOT_EMAIL:-admin@loadsadar.asia}
    read -rsp "管理员密码（不会回显）: " BOOT_PW; echo
    [[ -n "$BOOT_PW" ]] || fail "管理员密码不能为空"
    BOOTSTRAP_ENABLED=true
  else
    BOOTSTRAP_ENABLED=false
    BOOT_USER=admin
    BOOT_EMAIL=admin@loadsadar.asia
    BOOT_PW=""
  fi

  log "3/5 写入 $ENV_FILE（chmod 600）"
  cat > "$ENV_FILE" <<EOF
# 由 20-deploy-api.sh 生成。修改后 sudo systemctl restart watermark-api 生效。
WM_PROFILE=prod
SERVER_PORT=8080

WM_DATASOURCE_URL=jdbc:mysql://127.0.0.1:3306/${WM_DB_NAME}?useUnicode=true&characterEncoding=utf8&serverTimezone=UTC
WM_DATASOURCE_USERNAME=${WM_DB_USER}
WM_DATASOURCE_PASSWORD=${WM_DB_PASSWORD}

WM_REDIS_HOST=127.0.0.1
WM_REDIS_PORT=6379
WM_REDIS_PASSWORD=

WM_INSTANCE_PATH=${DATA_DIR}

WM_STORAGE_BACKEND=cos
WM_COS_SECRET_ID=${WM_COS_SECRET_ID}
WM_COS_SECRET_KEY=${WM_COS_SECRET_KEY}
WM_COS_REGION=${WM_COS_REGION}
WM_COS_BUCKET=${WM_COS_BUCKET}
WM_COS_STS_DURATION=15m

WM_CORS_ENABLED=true
WM_CORS_ALLOWED_ORIGINS=https://loadsadar.asia,https://www.loadsadar.asia

# Nginx 反代时识别 HTTPS（Spring Boot  relaxed binding → server.forward-headers-strategy）
SERVER_FORWARD_HEADERS_STRATEGY=framework
# www 全站走 Java 同域时可 lax；若页面与 API 分属不同子域且跨站调 API，请改为 none
WM_SESSION_COOKIE_SAME_SITE=lax

WM_BOOTSTRAP_ADMIN_ENABLED=${BOOTSTRAP_ENABLED}
WM_BOOTSTRAP_ADMIN_USERNAME=${BOOT_USER}
WM_BOOTSTRAP_ADMIN_EMAIL=${BOOT_EMAIL}
WM_BOOTSTRAP_ADMIN_PASSWORD=${BOOT_PW}
EOF
  chmod 600 "$ENV_FILE"
  chown root:root "$ENV_FILE"
else
  log "2-3/5 复用现有 env 文件"
fi

log "4/5 安装 systemd 单元"
cat > /etc/systemd/system/watermark-api.service <<'UNIT'
[Unit]
Description=Watermark Java API (Spring Boot)
After=network.target mysql.service redis-server.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/watermark-api
EnvironmentFile=-/opt/watermark-api/watermark-api.env
ExecStart=/usr/bin/java -XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -jar /opt/watermark-api/app.jar
Restart=on-failure
RestartSec=10
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable watermark-api
systemctl restart watermark-api

log "5/5 等待健康检查"
for i in {1..30}; do
  if curl -sf http://127.0.0.1:8080/actuator/health | grep -q '"status":"UP"'; then
    log "API 已 UP"
    curl -s http://127.0.0.1:8080/actuator/health
    echo
    exit 0
  fi
  sleep 2
done

warn "30 秒内未等到 UP，最后日志："
journalctl -u watermark-api -n 60 --no-pager
fail "API 启动失败，请排查后重跑本脚本"

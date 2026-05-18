#!/usr/bin/env bash
# 10-init-mysql.sh
# 创建 MySQL 数据库 watermark 与应用账户 watermark_app。
# 幂等：重复执行不会覆盖已有密码（若账户已存在）。
#
# 使用（二选一）：
#   1) 交互式：sudo bash 10-init-mysql.sh
#      会用 read -s 读入 watermark_app 密码（不进 bash history）。
#   2) 环境变量：sudo WM_DB_PASSWORD='强密码' bash 10-init-mysql.sh
#
# 脚本假设 Ubuntu 默认 auth_socket：root 可免密 `sudo mysql`。

set -euo pipefail
log() { printf "\n[\e[32m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
fail() { printf "\n[\e[31m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "必须以 root 运行：sudo bash $0"

DB_NAME="${WM_DB_NAME:-watermark}"
DB_USER="${WM_DB_USER:-watermark_app}"
if [[ -z "${WM_DB_PASSWORD:-}" ]]; then
  read -rsp "请输入 ${DB_USER} 的密码（强密码，不会回显）: " WM_DB_PASSWORD
  echo
  [[ -n "$WM_DB_PASSWORD" ]] || fail "密码不能为空"
fi

log "创建库 ${DB_NAME} 与用户 ${DB_USER}"
mysql <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${WM_DB_PASSWORD}';
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${WM_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

log "将 MySQL 连接信息写入 /etc/watermark/db.env（chmod 600）"
install -d -o root -g root -m 0755 /etc/watermark
cat > /etc/watermark/db.env <<EOF
# 由 10-init-mysql.sh 生成；勿手改密码后再执行本脚本，否则会覆盖回原值。
WM_DB_NAME=${DB_NAME}
WM_DB_USER=${DB_USER}
WM_DB_PASSWORD=${WM_DB_PASSWORD}
EOF
chmod 600 /etc/watermark/db.env

log "完成。watermark 库、${DB_USER} 账号已就绪；凭据已写入 /etc/watermark/db.env"

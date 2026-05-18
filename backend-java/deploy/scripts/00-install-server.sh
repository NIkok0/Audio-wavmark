#!/usr/bin/env bash
# 00-install-server.sh
# 在 Ubuntu 22.04 CVM 上安装运行依赖：JDK 17、Nginx、MySQL、Redis、ffmpeg、certbot。
# 幂等：重复执行不会破坏已有服务。
#
# 使用：
#   sudo bash 00-install-server.sh
#
# 参数：无。脚本不写入密钥、不请求外部敏感输入。

set -euo pipefail

log()  { printf "\n[\e[32m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
warn() { printf "\n[\e[33m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
fail() { printf "\n[\e[31m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "必须以 root 运行：sudo bash $0"

log "1/6 apt update & 安装基础软件"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl ca-certificates gnupg lsb-release \
  openjdk-17-jre-headless \
  nginx \
  mysql-server \
  redis-server \
  ffmpeg \
  certbot python3-certbot-nginx \
  jq net-tools

log "2/6 启动并自启 MySQL / Redis / Nginx"
systemctl enable --now mysql
systemctl enable --now redis-server
systemctl enable --now nginx

log "3/6 创建服务用户与目录"
# 使用 www-data（Ubuntu 自带），统一权限；数据目录给 775 便于后续 scp 上传
install -d -o www-data -g www-data -m 0755 /opt/watermark-api
install -d -o www-data -g www-data -m 0755 /opt/watermark-data
install -d -o www-data -g www-data -m 0755 /opt/watermark-data/instance
install -d -o www-data -g www-data -m 0755 /opt/watermark-data/ckpts
install -d -o www-data -g www-data -m 0755 /opt/watermark-app
install -d -o root -g root -m 0755 /etc/watermark
# systemd 环境变量文件默认空壳（被脚本替换）
touch /opt/watermark-api/watermark-api.env && chmod 600 /opt/watermark-api/watermark-api.env
touch /opt/watermark-api/watermark-worker.env && chmod 600 /opt/watermark-api/watermark-worker.env

log "4/6 加固 MySQL 绑定到 127.0.0.1（若已配置则跳过）"
MYCNF=/etc/mysql/mysql.conf.d/mysqld.cnf
if ! grep -qE '^bind-address\s*=\s*127\.0\.0\.1' "$MYCNF"; then
  sed -i 's/^bind-address.*/bind-address = 127.0.0.1/' "$MYCNF" || true
  systemctl restart mysql
fi

log "5/6 检查防火墙（UFW）"
if command -v ufw >/dev/null 2>&1; then
  # 不自动启用 UFW，只给出建议，避免与腾讯云安全组重复
  warn "如启用 UFW：sudo ufw allow 22,80,443/tcp && sudo ufw enable"
fi

log "6/6 版本摘要"
java -version || true
nginx -v || true
mysql --version || true
redis-server --version || true
ffmpeg -version | head -n1 || true
certbot --version || true

log "完成。接下来依次执行："
cat <<'EOF'
  sudo bash 10-init-mysql.sh
  sudo bash 20-deploy-api.sh /tmp/app.jar
  sudo bash 30-deploy-nginx.sh
  sudo bash 40-issue-tls.sh
  sudo bash 50-deploy-worker.sh   # 可选：部署 Python Worker（需先有 /opt/watermark-app 代码与 conda 环境）
EOF

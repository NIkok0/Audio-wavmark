#!/usr/bin/env bash
# 30-deploy-nginx.sh
# 写入两个站点的 Nginx 配置（api.loadsadar.asia 与 www.loadsadar.asia）并启用。
# 幂等；每次都会覆盖两个 site 文件，但不会删除 /etc/letsencrypt 证书。
#
# 本步骤只配置 HTTP（80）与 HTTPS 占位，TLS 证书由 40-issue-tls.sh 获取后 certbot 会自动改写 ssl_certificate 行。

set -euo pipefail
log() { printf "\n[\e[32m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
fail() { printf "\n[\e[31m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "必须以 root 运行：sudo bash $0"

API_DOMAIN="${WM_API_DOMAIN:-api.loadsadar.asia}"
WWW_DOMAIN="${WM_WWW_DOMAIN:-www.loadsadar.asia}"
BARE_DOMAIN="${WM_BARE_DOMAIN:-loadsadar.asia}"

log "为 ${API_DOMAIN} 写入 Nginx 站点"
cat > /etc/nginx/sites-available/${API_DOMAIN}.conf <<EOF
upstream watermark_api {
    server 127.0.0.1:8080;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name ${API_DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # HTTPS 就位前先直连（certbot 会自动加 301）
    location / {
        proxy_pass http://watermark_api;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        client_max_body_size 200m;
    }
}
EOF

log "为 ${WWW_DOMAIN} 写入 Nginx 站点（反代本机 8080：Spring Boot Thymeleaf + /api/v1/**）"
cat > /etc/nginx/sites-available/${WWW_DOMAIN}.conf <<EOF
upstream watermark_java_www {
    server 127.0.0.1:8080;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name ${BARE_DOMAIN} ${WWW_DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    client_max_body_size 500m;

    location / {
        proxy_pass http://watermark_java_www;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
EOF

log "启用站点并移除默认站点"
ln -sf /etc/nginx/sites-available/${API_DOMAIN}.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/${WWW_DOMAIN}.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

log "nginx -t && reload"
nginx -t
systemctl reload nginx

log "完成。可访问 http://${API_DOMAIN}/actuator/health 与 http://${WWW_DOMAIN}/health（Java 未启动时 502 正常）"

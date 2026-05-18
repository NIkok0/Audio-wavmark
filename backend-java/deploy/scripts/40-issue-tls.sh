#!/usr/bin/env bash
# 40-issue-tls.sh
# 使用 certbot 为 api.loadsadar.asia 和 www.loadsadar.asia 申请 Let's Encrypt 证书。
# 前置：DNS 已 A 记录到当前机器，80 端口能被公网访问，且 Nginx 站点已就位（跑过 30-deploy-nginx.sh）。
#
# 使用：
#   sudo EMAIL=you@example.com bash 40-issue-tls.sh

set -euo pipefail
log() { printf "\n[\e[32m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
fail() { printf "\n[\e[31m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "必须以 root 运行"
[[ -n "${EMAIL:-}" ]] || fail "请提供联系邮箱：sudo EMAIL=you@example.com bash $0"

API_DOMAIN="${WM_API_DOMAIN:-api.loadsadar.asia}"
WWW_DOMAIN="${WM_WWW_DOMAIN:-www.loadsadar.asia}"
BARE_DOMAIN="${WM_BARE_DOMAIN:-loadsadar.asia}"

log "为 ${API_DOMAIN} 申请证书"
certbot --nginx --non-interactive --agree-tos -m "$EMAIL" \
  --redirect \
  -d "$API_DOMAIN"

log "为 ${WWW_DOMAIN} 与 ${BARE_DOMAIN} 申请证书"
certbot --nginx --non-interactive --agree-tos -m "$EMAIL" \
  --redirect \
  -d "$WWW_DOMAIN" -d "$BARE_DOMAIN"

log "nginx -t && reload"
nginx -t
systemctl reload nginx

log "完成。检查："
echo "  curl -I https://${API_DOMAIN}/actuator/health"
echo "  curl -I https://${WWW_DOMAIN}"

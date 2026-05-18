# 一键部署脚本（Ubuntu 22.04 / 腾讯云 CVM）

本目录脚本覆盖 **Java API（含 Thymeleaf `www`）+ Python Worker + Nginx + TLS**。`www` 与 `api` 均由 Nginx 反代到本机 **8080**（同一 Spring Boot 进程），按编号顺序执行即可。

## 运行前提

- 操作系统：Ubuntu 22.04 LTS（其他版本需自行调整 apt 包名）
- 已在云厂商安全组放行 22 / 80 / 443
- DNS 已把 `api.loadsadar.asia` 和 `www.loadsadar.asia`（以及可选的 `loadsadar.asia`）解析到本机
- 有 root 权限

## 执行顺序

```bash
# 把本脚本包和 jar 都上传到 CVM 同一个目录（例如 /root/deploy）
cd /root/deploy

# 1. 基础软件
sudo bash 00-install-server.sh

# 2. MySQL 建库建账号（交互式输入密码；会写到 /etc/watermark/db.env）
sudo bash 10-init-mysql.sh
#    或非交互：sudo WM_DB_PASSWORD='强密码' bash 10-init-mysql.sh

# 3. 部署 Java API（会问 COS 凭据 + 是否 bootstrap 管理员）
sudo bash 20-deploy-api.sh ./app.jar

# 4. Nginx 站点（api + www → 127.0.0.1:8080）
sudo bash 30-deploy-nginx.sh

# 5. 签 TLS 证书
sudo EMAIL=you@example.com bash 40-issue-tls.sh

# 6. 部署 Python Worker（需仓库代码在 /opt/watermark-app 且已 conda create / pip install）
#    首次请 git clone 到 /opt/watermark-app 并创建 watermark conda 环境后再执行。
sudo bash 50-deploy-worker.sh
```

## 验证

```bash
# 本机
curl -sS http://127.0.0.1:8080/actuator/health
systemctl status watermark-api watermark-worker nginx

# 公网
curl -sS https://api.loadsadar.asia/actuator/health
curl -I https://www.loadsadar.asia
```

## 关键路径

| 路径 | 说明 |
|------|------|
| `/opt/watermark-api/app.jar` | Spring Boot 产物 |
| `/opt/watermark-api/watermark-api.env` | API 环境变量（chmod 600） |
| `/opt/watermark-api/watermark-worker.env` | Worker 环境变量（chmod 600） |
| `/opt/watermark-app` | Python Worker 与算法代码目录（`git clone`） |
| `/opt/watermark-data/instance` | 本机数据目录（对应 `WM_INSTANCE_PATH` / `INSTANCE_PATH`） |
| `/opt/watermark-data/ckpts` | 视频算法模型权重 |
| `/etc/watermark/db.env` | MySQL 库/账号/密码（chmod 600） |
| `/etc/systemd/system/watermark-*.service` | systemd 单元 |
| `/etc/nginx/sites-available/*.loadsadar.asia.conf` | Nginx 站点 |

## 回滚与排障

```bash
# 停服务
sudo systemctl stop watermark-api watermark-worker

# 看日志
journalctl -u watermark-api -n 200 --no-pager
journalctl -u watermark-worker -n 200 --no-pager

# 重新应用 env
sudo systemctl restart watermark-api

# 卸载（谨慎）
sudo systemctl disable --now watermark-api watermark-worker
sudo rm /etc/systemd/system/watermark-{api,worker}.service
sudo systemctl daemon-reload
sudo rm -rf /opt/watermark-api /opt/watermark-app  # 会删 jar 和代码
# 数据目录 /opt/watermark-data 和 MySQL 库请手工决定是否保留
```

## 安全事项

- MySQL 只监听 127.0.0.1（`00-install-server.sh` 会改 `bind-address`）
- `/opt/watermark-api/*.env`、`/etc/watermark/db.env` 一律 600
- bootstrap 管理员只在「空库首次」启用，建完立刻把 `WM_BOOTSTRAP_ADMIN_ENABLED=false` 并移除密码
- 腾讯云安全组不要对公网放行 3306 / 6379

#!/usr/bin/env bash
# 50-deploy-worker.sh
# 部署 Python Worker（消费 Redis Stream）：创建 conda 环境、装依赖、写 env 与 systemd。
#
# 前置：
#   1) 仓库已放在 /opt/watermark-app（手工 git clone 或 CI 同步）
#   2) ckpts/y_256b_img.pth 等模型文件已放到 /opt/watermark-data/ckpts/
#   3) 已跑 00/10/20 三步

set -euo pipefail
log() { printf "\n[\e[32m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
warn() { printf "\n[\e[33m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*"; }
fail() { printf "\n[\e[31m%s\e[0m] %s\n" "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "必须以 root 运行"

APP_DIR=/opt/watermark-app
CONDA_DIR=/opt/miniconda3
ENV_NAME=watermark
PYTHON_VERSION=3.9.23

[[ -d "$APP_DIR/watermark" ]] || fail "未找到 $APP_DIR/watermark（请先克隆仓库）"

# ---- 小内存机器加 swap：低于 4G 时临时扩到 6G 总 swap ----
MEM_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)
if [[ "$MEM_MB" -lt 3500 ]]; then
  CUR_SWAP_MB=$(awk '/SwapTotal/ {print int($2/1024)}' /proc/meminfo)
  if [[ "$CUR_SWAP_MB" -lt 4000 ]]; then
    log "内存仅 ${MEM_MB}MB，当前 swap ${CUR_SWAP_MB}MB，追加 4GB swapfile 以便 pip 装 torch"
    if [[ ! -f /swapfile-wm ]]; then
      fallocate -l 4G /swapfile-wm 2>/dev/null || dd if=/dev/zero of=/swapfile-wm bs=1M count=4096
      chmod 600 /swapfile-wm
      mkswap /swapfile-wm
      swapon /swapfile-wm
      if ! grep -q '/swapfile-wm' /etc/fstab; then
        echo '/swapfile-wm none swap sw 0 0' >> /etc/fstab
      fi
    else
      swapon /swapfile-wm 2>/dev/null || true
    fi
    free -h
  fi
fi

if ! command -v conda >/dev/null 2>&1 && [[ ! -x "$CONDA_DIR/bin/conda" ]]; then
  log "安装 Miniconda 到 $CONDA_DIR"
  curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p "$CONDA_DIR"
  rm -f /tmp/miniconda.sh
fi

export PATH="$CONDA_DIR/bin:$PATH"

# ---- 接受 Anaconda 官方 ToS（conda 25.x+ 非交互模式必需；以 root 身份接受） ----
log "接受 Anaconda ToS（以当前用户身份）"
"$CONDA_DIR/bin/conda" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main || true
"$CONDA_DIR/bin/conda" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r || true

# ---- conda 改清华镜像（避开官方 ToS 拦截 + 国内加速）----
log "配置 conda 清华镜像"
"$CONDA_DIR/bin/conda" config --remove-key channels 2>/dev/null || true
"$CONDA_DIR/bin/conda" config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
"$CONDA_DIR/bin/conda" config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
"$CONDA_DIR/bin/conda" config --set show_channel_urls yes

log "创建/更新 conda 环境 ${ENV_NAME}（Python ${PYTHON_VERSION}）"
if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  conda create -y -n "$ENV_NAME" python="${PYTHON_VERSION}"
fi

PIP="$CONDA_DIR/envs/$ENV_NAME/bin/pip"
PY="$CONDA_DIR/envs/$ENV_NAME/bin/python"

# ---- pip 改清华镜像（torch 等大 wheel 下载加速 5-10 倍）----
log "配置 pip 清华镜像"
"$PIP" config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
"$PIP" config set install.trusted-host pypi.tuna.tsinghua.edu.cn

log "安装依赖（requirements.txt）"
"$PIP" install --upgrade pip
"$PIP" install -r "$APP_DIR/requirements.txt"

# 重用 API 的数据库凭据
[[ -f /etc/watermark/db.env ]] || fail "未找到 /etc/watermark/db.env，请先执行 10-init-mysql.sh"
# shellcheck disable=SC1091
set -a; source /etc/watermark/db.env; set +a

# 重用 API 的 COS 凭据
API_ENV=/opt/watermark-api/watermark-api.env
[[ -f "$API_ENV" ]] || fail "未找到 $API_ENV，请先执行 20-deploy-api.sh"
WM_COS_SECRET_ID=$(grep '^WM_COS_SECRET_ID=' "$API_ENV" | cut -d= -f2-)
WM_COS_SECRET_KEY=$(grep '^WM_COS_SECRET_KEY=' "$API_ENV" | cut -d= -f2-)
WM_COS_REGION=$(grep '^WM_COS_REGION=' "$API_ENV" | cut -d= -f2-)
WM_COS_BUCKET=$(grep '^WM_COS_BUCKET=' "$API_ENV" | cut -d= -f2-)

WORKER_ENV=/opt/watermark-api/watermark-worker.env
log "写入 $WORKER_ENV"
cat > "$WORKER_ENV" <<EOF
SQLALCHEMY_DATABASE_URI=mysql+pymysql://${WM_DB_USER}:${WM_DB_PASSWORD}@127.0.0.1:3306/${WM_DB_NAME}?charset=utf8mb4
WM_REDIS_HOST=127.0.0.1
WM_REDIS_PORT=6379
WM_JOBS_STREAM_KEY=wm:stream:watermark
WM_JOBS_CONSUMER_GROUP=wm:workers
WM_JOBS_JOB_KEY_PREFIX=wm:job:
INSTANCE_PATH=/opt/watermark-data/instance
WM_STORAGE_BACKEND=cos
WM_COS_SECRET_ID=${WM_COS_SECRET_ID}
WM_COS_SECRET_KEY=${WM_COS_SECRET_KEY}
WM_COS_REGION=${WM_COS_REGION}
WM_COS_BUCKET=${WM_COS_BUCKET}
EOF
chmod 600 "$WORKER_ENV"
chown root:root "$WORKER_ENV"

log "安装 systemd 单元 watermark-worker"
cat > /etc/systemd/system/watermark-worker.service <<UNIT
[Unit]
Description=Watermark Python Worker (Redis Stream consumer)
After=network.target redis-server.service mysql.service
Wants=watermark-api.service

[Service]
Type=simple
User=www-data
WorkingDirectory=${APP_DIR}
EnvironmentFile=-${WORKER_ENV}
ExecStart=${PY} -m watermark.worker.redis_stream_worker
Restart=on-failure
RestartSec=10
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable watermark-worker
systemctl restart watermark-worker

sleep 2
systemctl --no-pager status watermark-worker | head -n 20 || true

log "完成。查看日志：journalctl -u watermark-worker -f"

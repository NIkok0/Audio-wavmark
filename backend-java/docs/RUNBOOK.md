# backend-java 运行手册（Runbook）

本文档面向值班与故障响应，聚焦“先止血、再定位、后复盘”。

- 架构背景与依赖边界：[`watermark-java-backend-tech-selection.md`](./watermark-java-backend-tech-selection.md)
- 生产部署与配置：[`DEPLOY-SERVER.md`](./DEPLOY-SERVER.md)
- 检查清单与测试基线：[`REQUIREMENTS-CHECKLIST-AND-TEST-CASES.md`](./REQUIREMENTS-CHECKLIST-AND-TEST-CASES.md)
- API 契约：[`API-CONTRACT.md`](./API-CONTRACT.md)
- 安全基线：[`SECURITY-BASELINE.md`](./SECURITY-BASELINE.md)
- 服务目标（SLO/SLA）：[`OPERATIONS-SLO-SLA.md`](./OPERATIONS-SLO-SLA.md)

---

## 1. 值班入口（5 分钟确认）

1. API 进程是否存活：`systemctl status watermark-api`
2. Worker 进程是否存活：`systemctl status watermark-worker`
3. 健康检查是否可达：`/actuator/health`
4. 任务是否堆积：Redis Stream backlog、任务状态停留在 `queued`
5. 外部依赖是否异常：MySQL / Redis / COS

---

## 2. 告警分级与响应时限

| 级别 | 典型场景 | 首次响应 | 处理目标 |
|------|----------|----------|----------|
| P0 | API 全量不可用、任务全阻塞、数据损坏风险 | 5 分钟内 | 15 分钟内止血 |
| P1 | 核心路径失败率显著升高、部分接口不可用 | 10 分钟内 | 30 分钟内恢复 |
| P2 | 非核心功能退化、偶发失败 | 30 分钟内 | 当日修复或给出绕行 |

---

## 3. 常见故障处理 SOP

### 3.1 API 不可用

- 现象：`/actuator/health` 不通或非 `UP`
- 快速动作：
  - `journalctl -u watermark-api -e --no-pager`
  - 检查 env 与数据库连接配置
  - 必要时重启：`systemctl restart watermark-api`
- 升级条件：重启后 5 分钟内仍未恢复

### 3.2 任务堆积（Worker 不消费）

- 现象：`queued` 持续增长，处理时延超阈值
- 快速动作：
  - `systemctl status watermark-worker`
  - 检查 Worker 日志、Redis 可达性、算法运行依赖
  - 必要时重启 Worker：`systemctl restart watermark-worker`
- 升级条件：重启后 backlog 继续增加

### 3.3 对象存储失败（COS/MinIO）

- 现象：上传完成、下载链接或结果回传失败
- 快速动作：
  - 核对 `WM_STORAGE_BACKEND` 与 COS/MinIO 凭证
  - 检查存储侧访问策略、桶权限、时钟偏差
  - 在 API 日志中定位具体错误码

---

## 4. 应急止血策略

- 降级入口：临时关闭高风险写路径或非核心任务入口
- 限流策略：收紧高成本接口（上传、入队、下载签名）
- 回滚策略：回滚到上一个稳定 Jar 与 env 版本
- 隔离策略：先恢复读能力，再逐步恢复写能力

---

## 5. 事件复盘模板

- 事件编号：
- 影响范围：
- 开始/恢复时间：
- 根因：
- 临时修复：
- 永久修复：
- 文档更新项（必须）：
  - 是否更新 `RUNBOOK.md`
  - 是否更新 `REQUIREMENTS...md`
  - 是否新增 ADR（见 `docs/adr/`）

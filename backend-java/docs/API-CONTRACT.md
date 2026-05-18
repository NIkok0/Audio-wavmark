# backend-java API 契约（Contract）

本文档定义核心接口契约与跨团队约定；完整字段以 OpenAPI 实时定义为准。

- OpenAPI：`/v3/api-docs`
- Swagger：`/swagger-ui.html`
- 生产部署：[`DEPLOY-SERVER.md`](./DEPLOY-SERVER.md)
- 安全基线：[`SECURITY-BASELINE.md`](./SECURITY-BASELINE.md)

---

## 1. 契约原则

- 统一前缀：`/api/v1`
- 幂等写接口需支持 `Idempotency-Key`
- 错误响应统一 `ProblemDetail`（RFC 7807）
- 版本演进遵循“向后兼容优先”

---

## 2. 核心接口分组

### 2.1 认证与会话

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`

### 2.2 文件与对象存储

- `POST /api/v1/files`
- `POST /api/v1/files/complete`
- `GET /api/v1/files`
- `DELETE /api/v1/files/{id}`

### 2.3 水印任务

- `POST /api/v1/jobs/watermark`
- `GET /api/v1/jobs/{jobId}`

### 2.4 管理接口

- `GET /api/v1/admin/**`
- `POST/PATCH /api/v1/admin/**`

---

## 3. 请求与响应样例（待补全）

> 约定：每个核心接口至少保留 1 组成功样例 + 1 组失败样例。

### 3.1 `POST /api/v1/jobs/watermark`（示例骨架）

请求头：

- `Content-Type: application/json`
- `Idempotency-Key: <uuid>`

请求体（示例）：

```json
{
  "fileId": 123,
  "operation": "embed",
  "algorithm": "wavmark"
}
```

成功响应（示例）：

```json
{
  "jobId": "uuid",
  "status": "queued"
}
```

---

## 4. 错误模型与异常码

- 统一字段：`type`、`title`、`status`、`detail`、`instance`
- 建议维护业务错误码映射表（HTTP 状态码 + 业务码 + 可重试性）
- 对 Agent/Tool 调用需明确“可重试”和“不可重试”边界

---

## 5. 与 Python Worker 契约边界

- 队列消息结构与 Redis Key 约定以技术选型文档 §10 为准
- Java 负责鉴权、入队、状态管理；Worker 负责算法执行与结果回写
- 任一字段变更必须同步更新：
  - 本文档
  - `watermark-java-backend-tech-selection.md`
  - 对应测试用例与回归脚本

---

## 6. 变更流程

1. 先更新 OpenAPI 与本契约文档。
2. 同步更新自动化测试。
3. 在 PR 描述中标注“兼容性影响”。
4. 重大变更新增 ADR（`docs/adr/`）。

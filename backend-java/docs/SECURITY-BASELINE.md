# backend-java 安全基线

本文档定义 `backend-java` 的最低安全要求，用于开发、自测、发布评审与审计对齐。

- 选型与架构背景：[`watermark-java-backend-tech-selection.md`](./watermark-java-backend-tech-selection.md)
- 生产配置与部署：[`DEPLOY-SERVER.md`](./DEPLOY-SERVER.md)
- 检查与测试：[`REQUIREMENTS-CHECKLIST-AND-TEST-CASES.md`](./REQUIREMENTS-CHECKLIST-AND-TEST-CASES.md)

---

## 1. 认证与会话

- 默认模式：Session + Redis（多实例会话外置）
- 密码策略：BCrypt；历史哈希采用兼容迁移策略
- 管理接口必须要求管理员角色
- 严禁在日志记录明文密码、密钥、完整会话标识

---

## 2. CSRF / CORS / Cookie

- Cookie Session 场景启用 CSRF 或等价防护
- CORS 仅允许显式白名单域名，禁止 `allowCredentials=true` 配 `*`
- Cookie 要求：
  - 生产环境启用 `Secure`
  - 按跨域策略设置 `SameSite`
  - 仅在必要范围设置 Domain/Path

---

## 3. 密钥与配置管理

- 敏感配置仅允许来自环境变量/Secret 管理系统
- 禁止提交到 Git：
  - 数据库密码
  - COS/MinIO 密钥
  - JWT/会话相关密钥
- 生产环境变量必须最小权限、最小暴露

---

## 4. 访问控制与最小权限

- API 按角色与资源归属双重校验
- 对象存储权限最小化（桶、前缀、动作粒度）
- 运维入口（SSH、控制台、数据库）按最小人员授权

---

## 5. 依赖与供应链安全

- 建议在 CI 开启依赖漏洞扫描
- 关键依赖升级需验证兼容性与安全公告
- 构建产物需可追溯到 commit 与构建日志

---

## 6. 安全事件响应要求

- 高危事件需 24h 内给出初步结论
- 所有事件必须产出复盘与改进项
- 影响鉴权/权限/数据完整性的改动必须补 ADR

---

## 7. 发布前安全检查（最小清单）

- [ ] 生产 `WM_*` 敏感变量不在仓库或日志暴露
- [ ] `/api/v1/admin/**` 权限校验有效
- [ ] CSRF/CORS/Cookie 策略与部署形态一致
- [ ] Actuator 暴露范围符合环境要求
- [ ] 安全组未暴露 MySQL/Redis 至公网

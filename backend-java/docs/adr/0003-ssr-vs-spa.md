# ADR-0003：SSR（Thymeleaf）vs SPA

- 状态：Accepted
- 日期：2026-05-18
- 关联文档：[`../watermark-java-backend-tech-selection.md`](../watermark-java-backend-tech-selection.md)

## 背景

项目处于快速落地阶段，既要保证管理端可用，也要兼顾 API 能力扩展。

## 备选方案

1. Thymeleaf SSR + 同进程 API
2. 前后端完全分离 SPA + API

## 决策

当前阶段采用 **Thymeleaf SSR + 同进程 API**。

## 理由

- 交付路径短，上线速度快
- Session 与同源部署配合简单
- 可在后续逐步演进为前后端分离

## 影响

- 需在文档中明确该方案与“默认推荐 SPA”的差异
- 安全策略需重点覆盖 CSRF/CORS 与 Cookie 配置

## 后续动作

- 在 [`../REQUIREMENTS-CHECKLIST-AND-TEST-CASES.md`](../REQUIREMENTS-CHECKLIST-AND-TEST-CASES.md) 持续跟踪偏差项
- 若切换为 SPA，新增迁移 ADR（路由、鉴权、CSRF 策略变更）

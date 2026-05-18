# ADR-0001：Session（Redis）vs JWT

- 状态：Accepted
- 日期：2026-05-18
- 关联文档：[`../watermark-java-backend-tech-selection.md`](../watermark-java-backend-tech-selection.md)

## 背景

系统包含管理端与业务 API，当前以服务端会话为主，并已接入 Redis。

## 备选方案

1. Session + Spring Session Redis
2. JWT Access + Refresh
3. 混合模式（管理端 Session，开放 API JWT）

## 决策

当前阶段采用 **Session + Spring Session Redis** 作为默认方案。  
当出现多终端开放 API 场景时，可引入混合模式。

## 理由

- 与当前实现一致，迁移成本最低
- 吊销能力直接，运维复杂度可控
- 对 SSR 与同源部署路径友好

## 影响

- 需明确 Cookie、CSRF、SameSite 策略
- 前后端跨域形态变化时需复核安全配置

## 后续动作

- 在 [`../SECURITY-BASELINE.md`](../SECURITY-BASELINE.md) 固化配置要求
- 若引入 JWT，新增 ADR 并给出迁移窗口

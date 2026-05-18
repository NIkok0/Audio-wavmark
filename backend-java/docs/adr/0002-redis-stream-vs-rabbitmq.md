# ADR-0002：Redis Stream vs RabbitMQ

- 状态：Accepted
- 日期：2026-05-18
- 关联文档：[`../watermark-java-backend-tech-selection.md`](../watermark-java-backend-tech-selection.md)

## 背景

水印任务是长耗时异步链路，当前系统已依赖 Redis（Session、限流、任务态）。

## 备选方案

1. Redis Stream
2. RabbitMQ
3. Kafka

## 决策

当前阶段采用 **Redis Stream** 作为任务队列实现。

## 理由

- 复用现有 Redis 基础设施，降低运维成本
- 具备消费组能力，满足当前规模的异步编排
- 与现有 Worker 模式兼容

## 影响

- 需关注 backlog、消费失败重试与幂等处理
- 超过当前规模时需评估 RabbitMQ 演进

## 后续动作

- 在 [`../RUNBOOK.md`](../RUNBOOK.md) 增加队列堆积排障流程
- 在 [`../OPERATIONS-SLO-SLA.md`](../OPERATIONS-SLO-SLA.md) 固化任务时延与失败率目标

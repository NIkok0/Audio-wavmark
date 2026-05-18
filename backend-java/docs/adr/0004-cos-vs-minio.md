# ADR-0004：COS（生产）vs MinIO（开发）

- 状态：Accepted
- 日期：2026-05-18
- 关联文档：[`../watermark-java-backend-tech-selection.md`](../watermark-java-backend-tech-selection.md)

## 背景

系统需要对象存储承载上传源文件与处理结果，同时要求开发联调成本可控。

## 备选方案

1. 生产与开发均使用 COS
2. 生产 COS，开发/CI 使用 MinIO
3. 全环境 MinIO

## 决策

采用 **生产 COS，开发/CI MinIO** 的双轨方案。

## 理由

- 生产环境对齐云上能力（STS、权限、可观测、运维）
- 开发与 CI 保持低成本、低依赖
- 兼顾工程效率与生产一致性

## 影响

- 需维护两套配置与兼容性验证
- 接口契约要避免绑定某一存储厂商特性

## 后续动作

- 在 [`../DEPLOY-SERVER.md`](../DEPLOY-SERVER.md) 明确生产配置
- 在 [`../API-CONTRACT.md`](../API-CONTRACT.md) 固化上传/完成流程契约

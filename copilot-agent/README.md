# Watermark Copilot - Industrial Agent Roadmap

本项目是 Watermark 平台的运维 Copilot。目标不是通用聊天，而是：

- 受控访问白名单 API；
- 基于仓库文档做可靠检索；
- 对关键动作有安全闸门；
- 可观测、可评测、可逐步演进到工业级 Agent。

---

## 1. 核心定位

- **输入**：自然语言问题（运维排障、配置核对、状态查询）
- **能力**：`search_docs` + `http_get` + `http_post`（白名单）
- **安全边界**：
  - 不执行 Shell
  - 不访问任意 URL
  - 不读取仓库外路径
  - 危险 POST 需要显式确认
- **输出**：SSE 流式响应，带 `tool_start`/`tool_end`

---

## 2. 目标架构（纯文本示意图）

以下均为等宽字符框图，不依赖 Mermaid 渲染；重点描述运行时进程边界、模块依赖方向与控制面/数据面职责。


### 2.1 运行时容器（进程边界）

当前逻辑上包含两个可部署进程：`copilot-agent`（FastAPI）与 `backend-java`（Spring Boot）；MySQL/Redis/COS 为外部依赖，Python watermark worker 为异步执行面。

```
                         +----------------------------------+
                         | User / Browser / API Client      |
                         +----------------+-----------------+
                                          | HTTP(S)
                                          v
        +------------------------------------------------------------------+
        | 【进程】copilot-agent (FastAPI, /v1/chat SSE)                     |
        | · Agent Runner: tool loop / safety gate / conversation context   |
        | · Tools: search_docs / http_get / http_post                      |
        | · RAG: keyword + vector (LlamaIndex + Chroma)                    |
        | · Observability: Langfuse traces/spans                            |
        +------------------+----------------------+-------------------------+
                           |                      |
                           | REST (whitelist)     | retrieval
                           v                      v
         +------------------------------+    +----------------------------+
         | backend-java API             |    | Chroma Index               |
         | /api/v1/**, /actuator/health |    | storage/chroma             |
         +---------------+--------------+    +-------------+--------------+
                         |                                 |
                         |                                 | embedding cache
                         v                                 v
               +-------------------+              +------------------------+
               | MySQL / Redis /   |              | HF cache (F:\model)   |
               | COS / MinIO       |              +------------------------+
               +---------+---------+
                         |
                         | Redis Stream / DB state
                         v
      +---------------------------------------------------------------+
      | Python Worker (watermark.worker.redis_stream_worker)          |
      | 执行算法计算并回写 MySQL/COS                                   |
      +---------------------------------------------------------------+
```

### 2.2 `copilot-agent` 内部（模块与依赖方向）

依赖建议方向：`server` -> `agent` -> (`tools`, `rag`, `observability`, `checkpoint`)；其中 `tools` 负责外部调用，`rag` 负责文档检索，`observability` 负责旁路追踪，`checkpoint` 负责长流程恢复。

```
+---------------------------------------------------------------------+
| copilot_agent/server.py                                             |
| FastAPI 路由 / lifespan / SSE 输出                                  |
+--------------------------+------------------------------------------+
                           | 调用
                           v
+---------------------------------------------------------------------+
| copilot_agent/agent/runner.py                                       |
| LangGraph 编排 / safety_gate / 工具调度 / 结果拼装                   |
+----------+--------------------+-------------------+------------------+
           |                    |                   |
           v                    v                   v
+-----------------------------+ +-------------------------------+ +------------------------------+
| copilot_agent/tools/*       | | copilot_agent/rag/*           | | observability/langfuse_tracer|
| whitelist + http_get/post   | | ingest/index/retriever/keyword| | trace/span（旁路）            |
| 对 backend-java 受控访问     | | 混合检索与文档引用             | | 失败不阻断主流程              |
+--------------+--------------+ +---------------+---------------+ +------------------------------+
               |                                |
               v                                v
      backend-java API                    storage/chroma
                                          + HF cache(F:\model)

runner -> SQLite checkpoint (agent_checkpoint_path)
```

内部模块可以按“入口层 -> 编排层 -> 能力层 -> 基础设施层”理解，避免模块边界混杂：

- 入口层：`server.py`，只负责 HTTP/SSE 协议、生命周期与请求编解码。
- 编排层：`agent/runner.py`，只负责对话状态机、工具调度、安全闸门与响应拼装。
- 能力层：`tools/*` 与 `rag/*`，分别负责在线 API 调用与离线知识检索。
- 基础设施层：`observability/*`、`storage/chroma`、配置与环境变量，提供追踪和持久化能力。

#### 2.2.1 模块职责清单

- `copilot_agent/server.py`
  - 提供 `GET /health`、`POST /v1/chat`；
  - 维护 SSE 事件输出协议（`meta/token/tool_start/tool_end/done/error`）；
  - 不包含业务推理与工具细节。
- `copilot_agent/agent/runner.py`
  - 承载主流程：接收消息 -> 规划步骤 -> 调用工具 -> 汇总结果；
  - 实现安全约束（危险 `http_post` 需审批）；
  - 统一衔接 `tools`、`rag`、`observability`。
- `copilot_agent/tools/*`
  - 对 `backend-java` 提供白名单化 `http_get/http_post`；
  - 负责路径约束、参数校验、错误归一化；
  - 不反向依赖 `server`，避免协议层与工具层耦合。
- `copilot_agent/rag/*`
  - 负责文档 ingest、索引构建、关键词检索、向量检索与融合召回；
  - 输出可引用的片段和来源，不直接处理 SSE 输出；
  - 索引持久化到 `storage/chroma`。
- `copilot_agent/observability/langfuse_tracer.py`
  - 旁路采集 trace/span，记录 LLM/tool/error 链路；
  - 观测失败不阻断主流程。
- `agent_checkpoint_path`（SQLite）
  - 持久化 LangGraph 执行状态与 thread 上下文；
  - 支持中断恢复与长流程续跑。

#### 2.2.2 依赖方向（必须遵守）

```text
server -> agent -> (tools, rag, checkpoint)
   \         \-> observability (旁路)
    \-> observability (入口/生命周期旁路)
```

- 允许：`server` 调 `agent`；`agent` 调 `tools/rag/observability/checkpoint`。
- 允许：`tools`/`rag` 使用共享配置、基础工具库。
- 禁止：`tools` 直接调用 `server`；`rag` 直接依赖 HTTP 路由层；`observability` 反向控制业务分支。
- 原则：上层可依赖下层，下层不得反向依赖上层。

#### 2.2.3 一次请求的内部流转

1. `server` 接收 `/v1/chat`，构造上下文并开启 SSE。
2. `runner` 执行状态图（assistant/tool/safety_gate/checkpoint）。
3. 需要实时状态时走 `tools`（白名单 API），需要知识补全时走 `rag`（索引检索）。
4. `runner` 汇总答案与工具事件，`server` 按协议流式返回。
5. `observability` 全程旁路记录，不改变主业务行为。

### 2.3 控制面与数据面（职责划分）

```
控制面（Control Plane）
- user question -> agent reasoning -> tool orchestration
- 安全规则（confirm_dangerous, whitelist）
- trace / eval / phase rollout

数据面（Data Plane）
- 文档检索：backend-java/docs -> chunks -> vector index
- 在线查询：backend-java API -> JSON state
- 任务执行：Redis Stream -> Python worker -> MySQL/COS
```

### 2.4 读图要点

- `copilot-agent` 不直接执行系统命令，所有外部访问通过受控工具完成。
- RAG 与在线 API 查询并存：文档负责“已知知识”，API 负责“实时状态”。
- 向量索引持久化在仓库 `storage/chroma`，模型缓存固定在 `F:\model`。
- Phase 演进（3-4 阶段）是在这个架构上增量升级编排与评测，不推倒重来。

---

## 3. Phase 规划

### Phase 0 - Baseline（已完成）

**目标**：跑通可用的最小运维 Copilot。

- FastAPI + SSE 聊天接口
- 文档分块检索（关键词）
- 白名单 HTTP 工具
- `confirm_dangerous` 安全闸门
- `docs/copilot-eval.md` 作为验收基线

**验收**：

- 可回答固定运维问题（含文档引用）
- 未授权路径/动作被拒绝

---

### Phase 1 - 可观测性（已完成）

**目标**：每轮对话可追踪，定位问题可观测。

- 集成 Langfuse trace/span
- 记录 LLM 轮次、tool 调用、错误路径
- 脱敏处理（cookie/password/set-cookie）
- 启动与退出时安全 flush

**关键文件**：

- `copilot_agent/observability/langfuse_tracer.py`
- `copilot_agent/agent/runner.py`
- `copilot_agent/server.py`

**验收**：

- Langfuse 可见完整对话链路
- 观测关闭时不影响主流程

---

### Phase 2 - Hybrid RAG（已完成）

**目标**：升级为“关键词 + 向量”的混合检索，提升召回与鲁棒性。

- 新增 RAG 模块化结构：
  - `rag/ingest.py`（文档装载与分块）
  - `rag/keyword.py`（关键词打分）
  - `rag/index.py`（Chroma 持久化索引）
  - `rag/retriever.py`（融合检索）
  - `rag/schema.py`（`DocChunk` 与格式化）
- 保持 `search_docs` 外部行为兼容（返回 excerpt + sources）
- 支持指纹比较，文档未变时直接复用索引

**当前状态**：

- Chroma 索引已构建：`copilot-agent/storage/chroma`
- 模型缓存迁移到：`F:\model`（不再依赖 C 盘缓存）

**验收**：

- `build_rag_store()` 可返回 `vector_enabled=True`
- 对关键问题检索命中与可解释性提升

---

### Phase 3 - Agent 编排升级（已完成）

**目标**：从线性 tool loop 进化到可维护的图编排（LangGraph）。

- 抽象 state / nodes / edges
- 增加 human-in-the-loop 节点（危险动作审批）
- 支持 checkpoint、恢复与长流程
- 保持现有 API 协议不变

**已完成（Step 1 / Step 2 / Step 3 / Step 4 / Step 5）**：

- 已切换为 LangGraph `assistant -> tools -> assistant` 状态图执行。
- 已引入可持久化 checkpoint（SQLite，配置项 `agent_checkpoint_path`）。
- `/v1/chat` 的 SSE 事件协议保持兼容（`token` / `tool_start` / `tool_end` / `done`）。
- 已增加图级 `safety_gate` 节点：危险 `http_post`（如 `/api/v1/jobs/watermark`）在进入 tools 前先经过审批拦截。
- 已提供 `scripts/verify_phase3_checkpoint.py`，可验证同一 `thread_id` 下状态恢复与 SQLite checkpoint 落盘。
- 已接入 CI：`.github/workflows/copilot-agent-phase3-ci.yml` 自动执行 Phase 3 编排回归（checkpoint + safety_gate）。
- CI 状态与指标口径见：`docs/ci-status.md`（不在 README 顶部堆徽章，避免干扰主文档叙事）。

**验收**：

- 编排图可替代现有循环逻辑
- 失败重试与中断恢复可验证

**Step 4 验收命令**：

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 python scripts/verify_phase3_checkpoint.py
```

**Step 4b 安全闸门回归命令**：

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 python scripts/verify_phase3_safety_gate.py
```

**Step 5 CI 验收**：

- 提交 PR 后，GitHub Actions 工作流 `copilot-agent Phase3 orchestration CI` 会自动运行。
- 该工作流会安装最小 Phase 3 依赖并执行：
  - `scripts/verify_phase3_checkpoint.py`（checkpoint 恢复）
  - `scripts/verify_phase3_safety_gate.py`（危险 `http_post` 拦截）
- Phase 3 产物统一输出到：`artifacts/phase3/`（summary/result 文件）。

---

### Phase 4 - 质量闭环（已落地，持续迭代）

**目标**：构建“可量化改进”闭环。

- 将 `docs/copilot-eval.md` 结构化为可执行数据集
- 引入 RAGAS 评测（faithfulness/context relevance）
- 加入规则检查（工具命中率、禁止调用）
- 输出每次变更前后对比报告

**已完成（Step 1 / Step 2 / Step 3 / Step 4）**：

- 已新增结构化评测数据集：`eval/phase4-eval-cases.json`（由 `docs/copilot-eval.md` 转换）。
- 已新增自动校验脚本：`scripts/verify_phase4_dataset.py`（schema/规则覆盖/安全阻断样例完整性）。
- 已新增 RAG 质量评测脚本：`scripts/verify_phase4_ragas.py`（默认离线 proxy 指标，支持可选 RAGAS 实评分）。
- 已新增统一汇总脚本：`scripts/verify_phase4_overall.py`（规则检查 + 趋势对比 + `phase4-overall-summary.json`）。
- 已新增 baseline 刷新脚本：`scripts/refresh_phase4_baseline.py`（将通过后的指标写回 `eval/phase4-baseline.json`）。
- 已接入 CI：`.github/workflows/copilot-agent-phase4-ci.yml`，自动输出 `phase4_dataset=PASS|FAIL`、`phase4_ragas=PASS|FAIL`、`phase4_overall=PASS|FAIL`，并在 `main/master` push 成功后自动刷新 baseline。
- CI 状态与指标口径见：`docs/phase4-ci-status.md`。

**Step 1 验收命令**：

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 python scripts/verify_phase4_dataset.py
```

**Step 2 验收命令（默认离线 proxy）**：

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 python scripts/verify_phase4_ragas.py --mode proxy --disable-vector
```

**Step 2 可选 RAGAS 实评分**：

```powershell
cd E:\code\watermarking
conda run -n myenv39 python -m pip install -r copilot-agent/requirements-phase4.txt
$env:OPENAI_API_KEY="sk-..."
conda run -n myenv39 python copilot-agent/scripts/verify_phase4_ragas.py --mode ragas
```

**Step 3 验收命令（统一总报告）**：

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 python scripts/verify_phase4_overall.py `
  --dataset eval/phase4-eval-cases.json `
  --dataset-summary artifacts/phase4/phase4-dataset-summary.json `
  --ragas-summary artifacts/phase4/phase4-ragas-summary.json `
  --baseline-json eval/phase4-baseline.json `
  --summary-json artifacts/phase4/phase4-overall-summary.json
```

**Step 4 验收命令（刷新 baseline）**：

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 python scripts/refresh_phase4_baseline.py `
  --overall-summary artifacts/phase4/phase4-overall-summary.json `
  --baseline-json eval/phase4-baseline.json
```

> CI 中 Step 4 只在 `push` 到 `main/master` 且 Step 1/2/3 全部通过时执行。

**验收**：

- 每次升级有可量化指标
- 回归失败可快速定位到检索/工具/提示词层

---

## 4. 环境与依赖

### Python 环境（推荐）

- Conda 环境：`myenv39`
- Python：`3.9.23`

```powershell
conda activate myenv39
```

### 依赖安装

```powershell
cd E:\code\watermarking
conda run -n myenv39 python -m pip install -r requirements.txt
```

> 说明：根目录 `requirements.txt` 已包含 `-r copilot-agent/requirements.txt` 引用。
>
> 若需要 Phase 4 的可选 RAGAS 实评分依赖，再额外执行：
>
> ```powershell
> conda run -n myenv39 python -m pip install -r copilot-agent/requirements-phase4.txt
> ```

### 关键依赖（Phase 2）

- `llama-index-core`
- `llama-index-vector-stores-chroma`
- `llama-index-embeddings-huggingface`
- `chromadb`
- `sentence-transformers`

---

## 5. 存储路径约定

- **向量索引（Chroma）**：
  - `E:\code\watermarking\copilot-agent\storage\chroma`
- **模型缓存（HuggingFace）**：
  - `F:\model`（`HF_HOME`）
- **Phase 回归产物**：
  - `E:\code\watermarking\copilot-agent\artifacts\phase3`
  - `E:\code\watermarking\copilot-agent\artifacts\phase4`

> 已在代码启动时自动应用缓存路径，避免默认落到 C 盘。

---

## 6. 运行方式

### 启动前准备

1. 启动 Java API（`backend-java`）
2. 配置 `copilot-agent/.env`（至少 `OPENAI_API_KEY`、`WATERMARK_API_BASE_URL`）

示例：

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
WATERMARK_API_BASE_URL=http://127.0.0.1:8080

# RAG
RAG_USE_VECTOR=true
RAG_REBUILD_INDEX=false
RAG_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
HF_HOME=F:\model

# Langfuse (可选)
LANGFUSE_ENABLED=true
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
```

### 启动服务

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 uvicorn copilot_agent.server:app --host 0.0.0.0 --port 8090
```

### 构建/重建向量索引

```powershell
cd E:\code\watermarking\copilot-agent
conda run -n myenv39 python scripts/build_index.py
```

---

## 7. API 概览

- `GET /health`：服务健康检查
- `POST /v1/chat`：对话接口（SSE）
  - 输入：`messages`、可选 `conversation_id`、可选 `confirm_dangerous`
  - 事件：`meta` / `token` / `tool_start` / `tool_end` / `done` / `error`

---

## 8. 安全约束

- 仅白名单 API 路径可调用（见 `tools/whitelist.py`）
- Session cookie 仅服务端内存保存
- 敏感数据在日志与观测中脱敏
- `/api/v1/jobs/watermark` 必须同时满足：
  - 服务端允许（`COPILOT_ALLOW_JOB_POST=true`）
  - 用户显式确认（`confirm_dangerous=true`）


---

## 9. 相关文件入口

- `copilot_agent/server.py`
- `copilot_agent/agent/runner.py`
- `copilot_agent/tools/http_tools.py`
- `copilot_agent/tools/whitelist.py`
- `copilot_agent/observability/langfuse_tracer.py`
- `copilot_agent/rag/`
- `scripts/build_index.py`
- `docs/copilot-eval.md`
- `docs/ci-status.md`
- `docs/phase4-ci-status.md`
- `eval/phase4-eval-cases.json`
- `eval/phase4-baseline.json`
- `scripts/verify_phase4_dataset.py`
- `scripts/verify_phase4_ragas.py`
- `scripts/verify_phase4_overall.py`
- `scripts/refresh_phase4_baseline.py`

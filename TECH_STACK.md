# 技术栈选型说明

隐私合规智能评审 AI 应用（Web 端 AI Chat 形态）的完整技术栈与选型理由。

## 总览

| 层 | 选型 | 说明 |
| --- | --- | --- |
| 前端 | React 18 + TypeScript + Vite + Ant Design X | AI 对话场景开箱即用 |
| 后端 | Python 3.11+ + FastAPI + Pydantic v2 | 原生 async，SSE 流式友好 |
| ORM | SQLAlchemy 2.0 + Alembic | 迁移管理 |
| 向量库 | PostgreSQL + pgvector | 业务数据与向量共库，运维简单 |
| 对象存储 | MinIO | 私有化原始文件存储 |
| 缓存/队列 | Redis + Celery | 文档解析/向量化异步任务 |
| LLM | MiniMax（M 系列，OpenAI 兼容）| Provider 抽象层，可切换 |
| 多模态 | MiniMax 视觉模型 + PaddleOCR 兜底 | 图片隐私合规识别 |
| Embedding | BGE-M3 | 中文语义强 |
| Rerank | BGE-reranker-v2 | 提升检索精度 |
| 编排 | LangChain / LangGraph（可选增强）| 多角色 Agent 编排 |
| 部署 | Docker + docker-compose + Nginx | 一键编排 |

## 前端

- **React 18 + TypeScript + Vite**：现代前端标配，冷启动快、类型安全。
- **Ant Design X + Ant Design 5**：阿里为 AI 对话场景打造，内置对话气泡、流式打字、附件上传、思维链/引用展示，显著减少对话 UI 开发量。
- **Tailwind CSS**：配合 AntD 做深色主题微调。
- **Zustand**：轻量状态管理，适合会话/消息状态。
- **TanStack Query + axios**：数据请求与缓存；流式回复走 `fetch` ReadableStream / SSE。
- **react-markdown + remark-gfm + rehype-highlight**：结构化评审意见渲染。

## 后端（Python）

- **FastAPI**：async 原生，SSE 流式支持好，自动 OpenAPI 文档。
- **SQLAlchemy 2.0 + Alembic**：ORM + 迁移。
- **JWT + RBAC**：三种角色（产品经理 / 测试工程师 / 法务）差异化权限与评审视角。
- **Celery + Redis**：文档解析、切片、向量化等耗时任务异步化。

## AI / RAG 能力层

- **LLM = MiniMax（可切换）**：通过统一 Provider 抽象层（OpenAI 兼容格式）接入，配置化可切 DeepSeek / 通义千问 / 私有化模型。**无 API Key 时自动降级为 Mock，用于离线自验证。**
- **多模态图片识别**：MiniMax 视觉模型理解图片内容，PaddleOCR 兜底提取文字。
- **Embedding = BGE-M3**：中文语义强，可 API 或本地部署；**离线降级为确定性本地向量**用于自验证。
- **Rerank = BGE-reranker-v2**：检索结果重排提升精度。
- **向量库 = PostgreSQL + pgvector**：`hnsw` 索引做向量相似度检索；**本地自验证降级为内存 numpy 余弦检索**。

## 文档解析

| 格式 | 库 |
| --- | --- |
| Word (.docx) | python-docx |
| PPT (.pptx) | python-pptx |
| Excel (.xlsx) | openpyxl |
| PDF | pypdf / PyMuPDF |
| WPS 私有格式 (.wps/.et/.dps) | LibreOffice headless 转标准格式再解析 |
| Markdown / 文本 | 内置解析 |
| 图片 | 多模态 VLM + OCR |

## 隐私合规特别设计

- **PII 脱敏层**：调用云端 LLM 前对手机号/身份证/邮箱等做脱敏占位替换。
- **模型可切换开关**：Provider 抽象层预留私有化模型接入位。
- **审计日志**：文档上传、评审、导出操作留痕。

## 本地自验证降级策略

| 组件 | 生产 | 本地自验证降级 |
| --- | --- | --- |
| LLM | MiniMax API | Mock Provider（无需 Key） |
| Embedding | BGE-M3 | 确定性哈希向量 |
| 向量库 | pgvector | 内存 numpy 余弦检索 |
| 数据库 | PostgreSQL | SQLite |
| 对象存储 | MinIO | 本地文件系统 |

通过环境变量自动判定，保证 `pytest` 与本地启动无需任何外部服务即可跑通端到端流程。

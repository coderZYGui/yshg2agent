# 技术栈

当前项目采用“本地优先单体应用”方案，目标是先满足 PRD/文档/图片隐私合规评审，而不是搭建复杂基础设施。

## 运行形态

| 层级 | 技术 | 说明 |
| --- | --- | --- |
| 前端 | React + TypeScript + Vite + Ant Design | Chat 工作台、知识库管理、结构化评审展示 |
| 后端 | Python + FastAPI | 鉴权、上传、解析、RAG 编排、SSE 输出 |
| 本地数据库 | SQLite | 保存用户、会话、消息、文档、chunks |
| 本地文件 | `backend/data/uploads` | 保存上传原文件 |
| 本地知识索引 | `backend/data/knowledge/chunks.json` | 保存可查看的知识库切片索引 |
| 文档解析 | python-docx、python-pptx、openpyxl、pypdf | 支持 Word、PPT、Excel、PDF、Markdown、文本 |
| 检索 | 本地 embedding + 进程内余弦相似度 | 无需 pgvector 或外部向量库 |
| LLM | OpenAI-compatible API 或 Mock | 配置 Key 后调用真实模型；无 Key 时本地 Mock |

## 为什么这样选

- SQLite 和本地文件足够支撑 MVP，部署和备份简单。
- 本地 `chunks.json` 让知识库索引可检查，便于排查评审依据。
- 进程内检索避免引入 PostgreSQL/pgvector，后续知识库变大后再升级。
- 同步解析足够支撑小到中等文档；如果后续出现大文件或多人并发，再引入后台任务。

## 后续可选升级

| 当前 | 可升级为 | 触发条件 |
| --- | --- | --- |
| SQLite | PostgreSQL | 多用户并发、权限隔离、审计要求上升 |
| 本地文件 | OSS/S3/MinIO | 多实例部署或文件量较大 |
| 本地检索 | pgvector / LanceDB / Chroma | 知识库规模大、检索质量不足 |
| 同步解析 | Celery/RQ/后台 worker | 大文件解析慢、上传请求超时 |
| Mock/单模型 | 多模型网关 | 需要成本、延迟、质量路由 |

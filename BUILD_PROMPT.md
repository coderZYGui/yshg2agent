# 项目构建提示词（可直接投喂给 AI 编程工具）

> 复制以下全部内容投喂给 Cursor / Claude Code 等 AI 编程工具，即可从零构建本应用。

---

## 角色

你是一名资深全栈 + AI 工程师，精通 Python/FastAPI、React/TypeScript、RAG 检索增强、LLM 应用工程与企业级隐私合规。请构建一个**企业级"隐私合规智能评审"AI Chat 应用**（Web 端，前后端分离）。

## 产品背景

面向企业内部三类用户，通过 AI 对话完成隐私合规评审：

- **产品经理**：审核新功能/产品方案的隐私风险，输出风险分析 + 整改方案 + 政策更新建议。
- **测试工程师**：审核代码、架构、权限实现中的隐私合规问题，提供具体整改建议。
- **法务**：审核隐私政策、信息保护规则、用户协议，提供修改建议和优化版本。

核心价值：用户上传 PRD 及相关文档（或图片），系统与"隐私合规知识库"（公司沉淀的隐私相关文档）比对，识别隐私合规问题、指出不符合项、给出结构化整改建议与引用来源。

## 技术栈（严格遵守）

- 前端：React 18 + TypeScript + Vite + Ant Design X + Ant Design 5 + Tailwind CSS + Zustand + TanStack Query；Markdown 用 react-markdown + remark-gfm + rehype-highlight。
- 后端：Python 3.11+ + FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + Uvicorn。
- 异步任务：Celery + Redis。
- LLM：MiniMax（M 系列，OpenAI 兼容 API），通过统一 Provider 抽象层接入，配置化可切换 DeepSeek/通义千问/私有化模型；**无 Key 时降级 Mock**。
- 多模态：MiniMax 视觉模型 + PaddleOCR 兜底。
- Embedding：BGE-M3；Rerank：BGE-reranker-v2。
- 向量库：PostgreSQL + pgvector（`hnsw` 索引）。
- 对象存储：MinIO。缓存：Redis。
- 文档解析：python-docx / python-pptx / openpyxl / pypdf；WPS 私有格式用 LibreOffice headless 转换；Markdown 内置。
- 部署：Docker + docker-compose + Nginx。

## 目录结构（monorepo）

```
project/
  backend/          FastAPI 后端
    app/
      main.py config.py database.py models.py schemas.py auth.py deps.py seed.py
      routers/      auth.py chat.py documents.py knowledge.py
      services/     llm.py embeddings.py vectorstore.py parser.py rag.py prompts.py redaction.py
    tests/
    requirements.txt .env.example
  frontend/         React 前端
    src/ (main.tsx App.tsx theme.ts api/ components/ pages/ store/)
    package.json vite.config.ts tsconfig.json index.html
  docker-compose.yml
```

## 核心功能需求

1. **多轮 Chat 对话**：SSE 流式回复；顶部/侧栏切换角色（产品/测试/法务），不同角色使用不同 System Prompt 与评审视角。
2. **多格式文档上传解析**：支持 Word/Excel/PPT/PDF/Markdown/图片；异步解析并展示进度。
3. **RAG 检索评审**：上传文档与用户提问，向量检索"隐私合规知识库"，rerank 后拼装上下文，LLM 生成评审。
4. **结构化评审输出**：返回风险项列表，每项含 `风险等级 / 问题定位 / 合规判定 / 整改建议 / 引用条款来源`。
5. **图片多模态识别**：识别截图/架构图内容做隐私合规检查。
6. **知识库管理**：上传/查看/删除公司沉淀的隐私合规文档，自动切片向量化入库。

## 数据模型

- `User(id, username, password_hash, role[pm|qa|legal], created_at)`
- `Conversation(id, user_id, title, role, created_at)`
- `Message(id, conversation_id, role[user|assistant|system], content, attachments, review_result, created_at)`
- `Document(id, owner_id, filename, mime, storage_path, kind[review|knowledge], parse_status, created_at)`
- `Chunk(id, document_id, seq, text, embedding[vector], metadata)`
- `ReviewResult(id, message_id, risk_level, location, verdict, suggestion, citations[jsonb])`
- `AuditLog(id, user_id, action, target, created_at)`

## 关键 API 契约

- `POST /api/auth/login` -> `{access_token, role}`；`POST /api/auth/register`
- `GET  /api/conversations` / `POST /api/conversations`
- `POST /api/chat/stream`（SSE）：`{conversation_id, role, message, document_ids?}` -> 流式 token + 末尾结构化 `review_result`
- `POST /api/documents/upload`（multipart）-> `{document_id, parse_status}`
- `GET  /api/documents/{id}` 解析状态与内容摘要
- `GET/POST/DELETE /api/knowledge`（知识库文档管理）
- `GET  /api/health`

## 三角色评审 System Prompt（内置）

为每个角色定制 System Prompt（详见 `services/prompts.py`）：产品经理侧重风险与整改+政策建议；测试工程师侧重代码/架构/权限实现的合规缺陷与具体修复；法务侧重政策/协议条款的合规性与优化版本。所有角色统一输出 JSON 结构化评审（风险等级/定位/判定/建议/引用）。

## RAG 流程规范

1. 知识库文档 -> 解析 -> 语义切片（500-800 字，重叠 80-120）-> BGE-M3 embedding -> pgvector 入库。
2. 查询：脱敏 -> embedding -> pgvector top-k 检索 -> BGE-reranker 重排 -> 取 top-n。
3. 拼装上下文（含引用元数据）-> 角色 System Prompt + 用户输入 + 上下文 -> LLM -> 解析 JSON 评审 -> 引用回填到检索片段。

## 隐私与可切换要求

- LLM 调用前经过 `redaction.py` 对 PII（手机号/身份证/邮箱/银行卡）脱敏。
- LLM/Embedding/向量库/DB/存储均做 Provider 抽象，通过环境变量在生产实现与本地降级实现间切换，保证无外部服务即可自验证。

## UI / 视觉规范

- **三栏布局**：左（角色切换 + 历史会话 + 知识库入口）| 中（SSE 对话主区 + 拖拽上传）| 右（结构化评审面板 + 引用来源 + 文档/图片预览）。
- **评审结果**：可展开的风险项卡片列表，可按风险等级筛选、导出。
- **深色科技风**（参考图：近黑背景 + 蓝色发光弧线）：
  - 背景 `#0A0A0B`/`#050506` + 径向蓝光；强调色蓝色渐变 `#3B82F6 → #60A5FA`。
  - 文字主 `#F5F5F7` 次 `#8A8A93`；卡片 `#141416` + `rgba(255,255,255,0.08)` 边框，圆角 12-16px，轻微毛玻璃。
  - 风险配色：高危 `#EF4444` / 中危 `#F59E0B` / 低危 `#3B82F6` / 合规 `#22C55E`。

## 验收标准

- `docker-compose up` 一键启动全部服务。
- 无 MiniMax Key 时后端以 Mock 模式运行，`pytest` 全绿，端到端可跑通"上传知识库 -> 上传 PRD -> 提问 -> 返回结构化评审"。
- 前端 `npm run build` 成功，三栏深色界面可交互，流式对话与风险卡片正常展示。

## 交付顺序

脚手架 -> 数据层与鉴权 -> 文档解析 -> RAG（embedding/向量库/检索）-> 对话（SSE + 角色 Prompt）-> 前端三栏 UI -> 联调与自验证。

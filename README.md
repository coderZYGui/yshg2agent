# 隐私合规智能评审 AI 应用

面向**产品经理 / 测试工程师 / 法务**的企业级隐私合规评审 AI Chat 应用。上传 PRD、政策、架构文档或图片，系统与内置的**隐私合规知识库**（RAG 检索）比对，识别隐私合规问题并输出**结构化评审意见**（风险等级 / 问题定位 / 合规判定 / 整改建议 / 引用来源）。

## 特性

- 多角色对话：产品经理 / 测试工程师 / 法务，各自专属评审视角与 System Prompt
- 多格式文档解析：Word / PPT / Excel / PDF / Markdown / 图片
- RAG 检索增强：上传文档与提问和隐私合规知识库比对
- 结构化评审：可展开风险项卡片 + 引用来源，可按风险等级筛选
- SSE 流式对话；深色科技风界面
- PII 脱敏层：调用云端 LLM 前对敏感信息脱敏
- 模型可切换：MiniMax / DeepSeek / 通义 / 私有化模型；**无 Key 自动降级 Mock**

## 技术栈

见 [TECH_STACK.md](TECH_STACK.md)。前端 React + TS + Vite + Ant Design；后端 Python + FastAPI；向量库 PostgreSQL + pgvector；对象存储 MinIO；缓存/队列 Redis + Celery。

## 目录结构

```
.
├── backend/            FastAPI 后端 (app/routers, app/services, tests)
├── frontend/           React 前端 (src/components, src/api, src/store)
├── docker-compose.yml  一键编排 (pgvector/redis/minio/backend/frontend)
├── BUILD_PROMPT.md     完整项目构建提示词 (交付物)
└── TECH_STACK.md       技术栈选型说明 (交付物)
```

## 本地开发运行（无需任何外部服务）

后端默认降级为 SQLite + Mock LLM + 本地 embedding，可直接跑通端到端。

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest        # 运行测试 (8 项)
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

演示账号：`pm/pm123`、`qa/qa123`、`legal/legal123`（首次启动自动创建并注入知识库样本）。

### 前端

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173 (已配置 /api 代理到 :8000)
```

## 生产部署（Docker）

```bash
# 可选: 配置真实模型 Key (留空则 Mock 模式)
export LLM_API_KEY=你的MiniMaxKey
docker compose up -d --build
```

- 前端： http://localhost:8080
- 后端 API 文档： http://localhost:8000/docs

## 切换到真实大模型

在 `backend/.env`（或 compose 环境变量）中填入：

```
LLM_API_KEY=...            # MiniMax API Key, 填入即从 Mock 切换为真实模型
LLM_BASE_URL=https://api.minimaxi.com/v1
LLM_MODEL=MiniMax-M1
EMBEDDING_API_KEY=...      # 填入即从本地哈希向量切换为 BGE-M3 等
DATABASE_URL=postgresql+psycopg://...   # 填入即从 SQLite 切换为 PostgreSQL + pgvector
```

## 自验证结果

- 后端 `pytest`：8 项全部通过（健康检查、注册登录、脱敏、切片、知识库入库、对话流返回结构化评审）
- 前端 `npm run build` + `tsc --noEmit`：通过
- 端到端：登录 → 检索知识库 → SSE 流式评审 → 结构化风险项 + 引用，跑通

# 隐私合规智能评审

面向产品经理、隐私测试工程师和法务的本地优先 AI Chat 应用。用户可以上传 PRD、政策、架构说明、Markdown、Office/PDF 文档或图片，系统会结合本地隐私合规知识库进行比对，并输出结构化评审意见。

## 简化后的架构

```text
React/Vite 前端
  -> FastAPI 本地后端
    -> backend/data/app.db                # SQLite，本地保存用户、会话、文档、切片
    -> backend/data/uploads/              # 本地上传文件
    -> backend/data/knowledge/chunks.json # 可查看的本地知识库切片索引
    -> LLM API 或 Mock                    # 无 Key 时自动 Mock
```

默认不依赖 PostgreSQL、pgvector、MinIO、Redis、Celery 或其他外部基础设施。

## 核心能力

- 三类角色 Prompt：产品经理、隐私测试工程师、法务。
- 知识库上传：把公司隐私合规资料解析、切片并保存到本地。
- PRD/附件上传：解析待评审文档，与本地知识库比对。
- Chat 对话：通过 SSE 返回评审结果。
- 结构化输出：风险等级、问题位置、合规判断、整改建议、引用来源。
- 图片附件：当前可登记图片内容；接入真实视觉模型后可做图片隐私合规识别。

## 本地启动

后端：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

前端：

```powershell
cd frontend
npm install
npm run dev
```

访问：

- 前端：http://localhost:5173
- 后端 API 文档：http://localhost:8000/docs

演示账号：

- `pm / pm123`
- `qa / qa123`
- `legal / legal123`

## 接入真实模型

在 `backend/.env` 中配置：

```env
LLM_API_KEY=你的模型Key
LLM_BASE_URL=https://api.minimaxi.com/v1
LLM_MODEL=MiniMax-M1
```

可选接入 embedding API：

```env
EMBEDDING_API_KEY=你的EmbeddingKey
EMBEDDING_BASE_URL=https://example.com/v1
EMBEDDING_MODEL=bge-m3
```

不配置 Key 时：

- LLM 使用 Mock 输出，便于本地演示。
- Embedding 使用本地 hash embedding，便于离线检索。

## Docker 单机运行

```powershell
docker compose up -d --build
```

访问：

- 前端：http://localhost:8080
- 后端：http://localhost:8000/docs

Docker 也只运行前端和后端两个容器，数据通过 `./backend/data:/app/data` 保存在本机。

## 数据位置

```text
backend/data/
  app.db
  uploads/
  knowledge/
    chunks.json
```

`chunks.json` 是知识库和上传文档解析后的本地切片索引，方便排查“模型参考了哪些资料”。

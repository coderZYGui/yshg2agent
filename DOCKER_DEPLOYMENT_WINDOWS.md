# Windows Docker Compose 部署手册

本项目会启动两个容器：

- `frontend`：React 页面，由 Nginx 提供服务，访问地址为 `http://localhost:8080`
- `backend`：FastAPI 接口，访问地址为 `http://localhost:8000`

SQLite 数据库和上传文件保存在电脑的 `backend/data` 目录。删除或重建容器不会删除这些数据。

## 一、第一次启动

### 1. 启动 Docker Desktop

等待 Docker Desktop 左下角显示 Docker Engine 正在运行，并确认使用的是 Linux containers。

### 2. 打开 PowerShell，进入项目目录

```powershell
cd C:\Users\guichaoyang\Desktop\yshg2agent
```

### 3. 准备环境变量

你的项目当前已经有 `backend/.env`，可以直接使用。以后如果在一台新电脑或服务器上部署，而这个文件不存在，再执行：

```powershell
Copy-Item .\backend\.env.example .\backend\.env
notepad .\backend\.env
```

至少需要填写以下配置，等号后面不要加引号：

```dotenv
SECRET_KEY=请替换为随机长字符串
LLM_PROVIDER=dashscope_app
DASHSCOPE_API_KEY=百炼API_KEY
DASHSCOPE_APP_ID=百炼应用ID
ALIBABA_CLOUD_ACCESS_KEY_ID=阿里云AccessKey_ID
ALIBABA_CLOUD_ACCESS_KEY_SECRET=阿里云AccessKey_Secret
BAILIAN_WORKSPACE_ID=百炼业务空间ID
```

`DASHSCOPE_API_KEY` 和 `DASHSCOPE_APP_ID` 用于调用百炼应用；阿里云 AccessKey 和 `BAILIAN_WORKSPACE_ID` 用于上传并解析附件。不要把 `backend/.env` 发给别人，也不要提交到 Git。

生成一个随机 `SECRET_KEY` 的 PowerShell 命令：

```powershell
$secretBytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($secretBytes)
[BitConverter]::ToString($secretBytes).Replace('-', '').ToLower()
```

把最后输出的一长串字符复制到 `SECRET_KEY=` 后面。

### 4. 检查配置

```powershell
docker compose config --quiet
```

没有任何输出就是通过。如果提示找不到 `backend/.env`，回到第 3 步创建它。

### 5. 构建并启动

```powershell
docker compose up -d --build
```

第一次启动会下载 Python、Node.js 和 Nginx 镜像，通常需要几分钟。命令结束后检查状态：

```powershell
docker compose ps
```

`backend` 和 `frontend` 都显示 `healthy` 后即可使用。

### 6. 打开服务

- 前端页面：`http://localhost:8080`
- 后端接口文档：`http://localhost:8000/docs`
- 后端健康检查：`http://localhost:8000/api/health`

健康检查返回的 `llm_mode` 应为 `dashscope_app`。如果显示 `mock`，说明 `DASHSCOPE_API_KEY` 或 `DASHSCOPE_APP_ID` 为空；如果显示 `dashscope_app` 但调用报错，请通过后端日志检查凭据、应用 ID 和百炼服务状态。

## 二、日常使用

启动已有容器：

```powershell
docker compose up -d
```

查看运行状态：

```powershell
docker compose ps
```

实时查看全部日志，按 `Ctrl+C` 只会退出日志查看，不会停止服务：

```powershell
docker compose logs -f
```

只查看后端日志：

```powershell
docker compose logs -f backend
```

停止并删除容器：

```powershell
docker compose down
```

这不会删除 `backend/data`。不要随意执行 `docker compose down -v`，也不要删除 `backend/data`，否则可能丢失 SQLite 数据和上传文件。

## 三、代码更新后重新部署

先备份数据：

```powershell
Copy-Item .\backend\data .\backend\data-backup -Recurse
```

然后重新构建并启动：

```powershell
docker compose up -d --build
docker compose ps
```

## 四、常见问题

### Docker 命令一直等待或提示无法连接

先确认 Docker Desktop 已完全启动。可运行：

```powershell
docker info
```

### 8000 或 8080 端口被占用

检查占用：

```powershell
Get-NetTCPConnection -LocalPort 8000,8080 -ErrorAction SilentlyContinue
```

关闭占用端口的程序，或者修改 `docker-compose.yml` 左侧端口。例如把 `127.0.0.1:8080:80` 改成 `127.0.0.1:8081:80`，同时把 `CORS_ORIGINS: http://localhost:8080` 改成 `CORS_ORIGINS: http://localhost:8081`，然后从 `http://localhost:8081` 访问。

### 页面打不开或接口报错

先执行：

```powershell
docker compose ps
docker compose logs --tail 200 backend
docker compose logs --tail 200 frontend
```

日志通常会直接说明是环境变量、网络、端口还是百炼凭据问题。

### 修改了 `.env` 但没有生效

环境变量在创建容器时载入，需要重新创建容器：

```powershell
docker compose up -d --force-recreate
```

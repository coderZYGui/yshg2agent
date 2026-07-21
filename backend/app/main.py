from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .access_gate import ACCESS_COOKIE_NAME, has_valid_access_gate
from .config import settings
from .database import SessionLocal, init_db
from .routers import access, auth, chat, conversations, documents, knowledge
from .seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

_ACCESS_PUBLIC_PATHS = {
    "/api/health",
    "/api/access/verify",
    "/api/access/status",
    "/api/access/logout",
}


@app.middleware("http")
async def require_access_gate(request: Request, call_next):
    path = request.url.path.rstrip("/") or "/"
    is_protected_api = path.startswith("/api/") and path not in _ACCESS_PUBLIC_PATHS
    if (
        request.method != "OPTIONS"
        and is_protected_api
        and not has_valid_access_gate(request.cookies.get(ACCESS_COOKIE_NAME))
    ):
        return JSONResponse(
            status_code=401,
            content={"detail": "请先完成访问校验"},
        )
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(access.router)
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(knowledge.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_mode": "mock" if settings.llm_is_mock else settings.llm_provider,
        "embedding_mode": "local" if settings.embedding_is_local else "api",
        "vector_backend": settings.resolved_vector_backend,
    }

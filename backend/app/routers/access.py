import hmac

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from ..access_gate import (
    ACCESS_COOKIE_NAME,
    create_access_gate_token,
    has_valid_access_gate,
)
from ..config import settings

router = APIRouter(prefix="/api/access", tags=["access"])


class VerifyAccessRequest(BaseModel):
    password: str


def _is_https_request(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    return request.url.scheme == "https" or forwarded_proto.split(",")[0].strip() == "https"


@router.post("/verify")
def verify_access(payload: VerifyAccessRequest, request: Request, response: Response):
    if not settings.access_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="访问密码尚未配置",
        )
    if not hmac.compare_digest(
        payload.password.encode("utf-8"), settings.access_password.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="访问密码错误",
        )

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=create_access_gate_token(),
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=_is_https_request(request),
        samesite="lax",
        path="/",
    )
    return {"success": True}


@router.get("/status")
def access_status(request: Request):
    return {
        "authenticated": has_valid_access_gate(
            request.cookies.get(ACCESS_COOKIE_NAME)
        )
    }


@router.post("/logout")
def logout_access(response: Response):
    response.delete_cookie(key=ACCESS_COOKIE_NAME, path="/")
    return {"success": True}

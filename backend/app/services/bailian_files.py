import asyncio
import hashlib
import time
from pathlib import Path

import httpx
from alibabacloud_bailian20231229 import models as bailian_models
from alibabacloud_bailian20231229.client import Client as BailianClient
from alibabacloud_tea_openapi import models as open_api_models

from ..config import settings


class BailianFileError(RuntimeError):
    pass


def _make_client():
    missing = []
    if not settings.alibaba_cloud_access_key_id:
        missing.append("ALIBABA_CLOUD_ACCESS_KEY_ID")
    if not settings.alibaba_cloud_access_key_secret:
        missing.append("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    if not settings.bailian_workspace_id:
        missing.append("BAILIAN_WORKSPACE_ID")
    if missing:
        raise BailianFileError("缺少百炼文件上传配置：" + "、".join(missing))

    config = open_api_models.Config(
        access_key_id=settings.alibaba_cloud_access_key_id,
        access_key_secret=settings.alibaba_cloud_access_key_secret,
        region_id=settings.bailian_region_id,
    )
    return BailianClient(config)


def _upload_binary(method, url, headers, file_path):
    with Path(file_path).open("rb") as file:
        response = httpx.request(
            method.upper(),
            url,
            headers=headers or {},
            content=file,
            timeout=120,
        )
    response.raise_for_status()


def _md5(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _headers(value) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    if hasattr(value, "to_map"):
        return {str(key): str(item) for key, item in value.to_map().items()}
    return {}


async def upload_session_file(path: str, filename: str) -> str:
    file_path = Path(path)
    if not file_path.is_file():
        raise BailianFileError(f"附件不存在：{filename}")

    client = _make_client()
    workspace_id = settings.bailian_workspace_id
    lease_request = bailian_models.ApplyFileUploadLeaseRequest(
        category_type="SESSION_FILE",
        file_name=filename,
        md_5=_md5(file_path),
        size_in_bytes=str(file_path.stat().st_size),
    )

    try:
        lease_response = await asyncio.to_thread(
            client.apply_file_upload_lease,
            "default",
            workspace_id,
            lease_request,
        )
        lease = lease_response.body.data
        if not lease or not lease.file_upload_lease_id or not lease.param:
            raise BailianFileError("百炼未返回有效的文件上传租约")

        await asyncio.to_thread(
            _upload_binary,
            lease.param.method,
            lease.param.url,
            _headers(lease.param.headers),
            file_path,
        )

        add_request = bailian_models.AddFileRequest(
            category_id="default",
            category_type="SESSION_FILE",
            lease_id=lease.file_upload_lease_id,
            parser="DASHSCOPE_DOCMIND",
        )
        add_response = await asyncio.to_thread(
            client.add_file,
            workspace_id,
            add_request,
        )
        file_id = getattr(add_response.body.data, "file_id", "")
        if not file_id.startswith("file_session_"):
            raise BailianFileError(
                "百炼返回的文件 ID 不是有效的 file_session_ 会话文件 ID"
            )

        deadline = time.monotonic() + settings.bailian_file_ready_timeout_seconds
        failed_statuses = {
            "PARSE_FAILED",
            "SAFE_CHECK_FAILED",
            "INDEX_BUILDING_FAILED",
            "INDEX_DELETED",
            "FILE_EXPIRED",
        }
        while time.monotonic() < deadline:
            describe_response = await asyncio.to_thread(
                client.describe_file,
                workspace_id,
                file_id,
                bailian_models.DescribeFileRequest(),
            )
            info = describe_response.body.data
            status = getattr(info, "status", "")
            if status == "FILE_IS_READY":
                return file_id
            if status in failed_statuses:
                detail = getattr(info, "parse_error_message", "") or status
                raise BailianFileError(f"附件解析失败：{detail}")
            await asyncio.sleep(settings.bailian_file_poll_interval_seconds)

        raise BailianFileError("等待附件解析完成超时")
    except BailianFileError:
        raise
    except Exception as exc:
        raise BailianFileError(f"百炼附件处理失败：{exc}") from exc

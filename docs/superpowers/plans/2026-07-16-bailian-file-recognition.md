# Bailian File Recognition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the existing DashScope SDK chat flow to answer questions about uploaded images and files using Bailian session files.

**Architecture:** Keep `Application.call` as the only agent invocation path. Add a focused Bailian OpenAPI SDK service that applies for a `SESSION_FILE` lease, uploads bytes to the returned pre-signed URL, calls `AddFile`, and polls `DescribeFile` until `FILE_IS_READY`; pass the resulting IDs through `rag_options.session_file_ids`. Images also retain the existing `image_list` path for vision-capable published agents.

**Tech Stack:** FastAPI, DashScope Python SDK, Alibaba Cloud Bailian 2023-12-29 Python SDK, httpx, pytest, React/TypeScript.

## Global Constraints

- Agent responses continue to use `dashscope.Application.call`; no direct HTTP implementation of the application completion API is added.
- Session files use `CategoryId=default` and `CategoryType=SESSION_FILE`.
- A file is sent to the agent only after `DescribeFile` reports `FILE_IS_READY`.
- Existing text-only and SSE streaming behavior remains unchanged.
- Existing uncommitted user changes are preserved and are not included in an automatic commit.

---

### Task 1: Bailian session-file service

**Files:**
- Create: `backend/app/services/bailian_files.py`
- Modify: `backend/app/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_bailian_files.py`

**Interfaces:**
- Produces: `upload_session_file(path: str, filename: str) -> str`.
- Raises: `BailianFileError` when credentials are absent, upload fails, parsing fails, the ID is invalid, or readiness times out.

- [ ] Write failing tests for MD5/lease parameters, pre-signed binary upload, `AddFile`, `file_session_` validation, readiness polling, and failure states.
- [ ] Run `backend/.venv/Scripts/python.exe -m pytest backend/tests/test_bailian_files.py -v` and confirm failures are caused by the missing service.
- [ ] Add `alibabacloud_bailian20231229>=2.14.0` and the environment settings `ALIBABA_CLOUD_ACCESS_KEY_ID`, `ALIBABA_CLOUD_ACCESS_KEY_SECRET`, `BAILIAN_WORKSPACE_ID`, and `BAILIAN_REGION_ID`.
- [ ] Implement the minimal SDK service and pre-signed binary upload with `httpx`.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Chat attachment integration

**Files:**
- Modify: `backend/app/services/llm.py`
- Modify: `backend/app/routers/chat.py`
- Test: `backend/tests/test_app.py`

**Interfaces:**
- Consumes: `bailian_files.upload_session_file`.
- Produces: all uploaded documents, images, audio, and video as ready `session_file_ids`; images additionally remain available as `image_list`.

- [ ] Write failing tests proving image files are included in session-file upload and upload errors are surfaced rather than silently ignored.
- [ ] Run the focused tests and confirm expected failures.
- [ ] Replace the legacy `/api/v1/files` upload helper with the Bailian session-file service.
- [ ] Upload every supported attachment, including images, before streaming the agent response.
- [ ] Emit an SSE `error` event with a useful message when preparation fails.
- [ ] Run focused backend tests and confirm they pass.

### Task 3: Frontend validation and failure feedback

**Files:**
- Modify: `frontend/src/components/ChatPanel.tsx`
- Modify: `frontend/src/api/client.ts`
- Test: existing frontend build and TypeScript checks.

**Interfaces:**
- Consumes: SSE `error` events.
- Produces: file-count, extension, and size validation before upload; visible server error text.

- [ ] Add accepted file extensions and the documented limits: 10 files; documents 100 MB; images 20 MB; audio/video 512 MB.
- [ ] Parse SSE `error` events in the client.
- [ ] Display the backend error and stop the sending state.
- [ ] Run `npm run build` in `frontend` and confirm success.

### Task 4: Verification

**Files:**
- Modify only tests if verification exposes a real regression.

- [ ] Run `backend/.venv/Scripts/python.exe -m pytest backend/tests -q`.
- [ ] Run `npm run build` in `frontend`.
- [ ] With real AccessKey credentials and Workspace ID configured, upload a text file containing a unique marker and confirm the answer returns it.
- [ ] Upload an image with a known title and confirm OCR/content recognition; report separately whether visual understanding is enabled in the published agent.
- [ ] Review the diff for unrelated changes, swallowed errors, leaked secrets, and missing status handling.

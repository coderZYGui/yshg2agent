"""多格式文档解析: Word / PPT / Excel / PDF / Markdown / 文本 / 图片。

WPS 私有格式(.wps/.et/.dps)生产环境通过 LibreOffice headless 转标准格式再解析。
"""

from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def parse_document(path: str, mime: str = "") -> str:
    ext = Path(path).suffix.lower()
    try:
        if ext == ".docx":
            return _parse_docx(path)
        if ext == ".pptx":
            return _parse_pptx(path)
        if ext == ".xlsx":
            return _parse_xlsx(path)
        if ext == ".pdf":
            return _parse_pdf(path)
        if ext in {".md", ".markdown", ".txt"}:
            return _parse_text(path)
        if ext in IMAGE_EXTS:
            return _parse_image(path)
        # 兜底: 尝试按文本读取
        return _parse_text(path)
    except Exception as exc:  # noqa: BLE001
        return f"[解析失败: {exc}]"


def _parse_docx(path: str) -> str:
    from docx import Document as Docx

    doc = Docx(path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def _parse_pptx(path: str) -> str:
    from pptx import Presentation

    prs = Presentation(path)
    parts = []
    for i, slide in enumerate(prs.slides, 1):
        parts.append(f"# 幻灯片 {i}")
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = "".join(run.text for run in para.runs).strip()
                    if text:
                        parts.append(text)
    return "\n".join(parts)


def _parse_xlsx(path: str) -> str:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    parts = []
    for ws in wb.worksheets:
        parts.append(f"# 工作表 {ws.title}")
        for row in ws.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None]
            if cells:
                parts.append(" | ".join(cells))
    wb.close()
    return "\n".join(parts)


def _parse_pdf(path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    parts = []
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            parts.append(f"# 第 {i} 页\n{text}")
    return "\n".join(parts)


def _parse_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def _parse_image(path: str) -> str:
    # 图片内容识别在对话链路中交由多模态 VLM 处理; 此处仅登记占位。
    return f"[图片文件: {Path(path).name}, 将在评审时由多模态模型识别内容]"


def chunk_text(text: str, size: int = 600, overlap: int = 100) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + size, n)
        chunks.append(text[start:end])
        if end >= n:
            break
        start = end - overlap
    return chunks

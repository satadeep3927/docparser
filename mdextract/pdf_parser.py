import pdfplumber
from collections import defaultdict

LINE_Y_TOLERANCE = 3
PARA_GAP_FACTOR = 1.4

# Minimum number of characters on a page before we consider it
# "has text" and skip OCR.
_MIN_CHARS_FOR_TEXT_PAGE = 20


def parse_pdf(
    file_path: str,
    ocr_lang: str = "eng",
    tessdata_dir: str | None = None,
) -> str:
    """Convert a PDF file to Markdown with heading detection and table support.

    Scanned pages (no embedded text) are automatically processed with OCR
    via Tesseract. Requires Tesseract to be installed on the system.

    Args:
        file_path:    Path to the PDF file.
        ocr_lang:     Tesseract language code(s) for scanned pages.
                      Single language:  ``"fra"`` (French), ``"eng"`` (English)
                      Multiple languages: ``"eng+fra"`` (English + French)
                      Defaults to ``"eng"``.
        tessdata_dir: Path to a custom ``tessdata`` directory, e.g.
                      ``r"C:\\Program Files\\Tesseract-OCR\\tessdata_best"``.
                      When ``None`` (default) Tesseract uses its built-in
                      ``tessdata`` folder (standard models).
    """
    md_pages = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            if len(page.chars) >= _MIN_CHARS_FOR_TEXT_PAGE:
                # Normal text-based page
                page_md = _process_page(page)
            else:
                # Scanned / image-only page — fall back to OCR
                page_md = _ocr_page(
                    file_path, page_num - 1,
                    lang=ocr_lang,
                    tessdata_dir=tessdata_dir,
                )

            if page_md.strip():
                md_pages.append(f"<!-- Page {page_num} -->\n\n{page_md}")
    return "\n\n---\n\n".join(md_pages)


# ---------------------------------------------------------------------------
# OCR fallback
# ---------------------------------------------------------------------------

def _ocr_page(
    file_path: str,
    page_index: int,
    lang: str = "eng",
    tessdata_dir: str | None = None,
) -> str:
    """Render a PDF page to an image and extract text via Tesseract OCR.

    Args:
        file_path:    Path to the source PDF.
        page_index:   Zero-based page index.
        lang:         Tesseract language string, e.g. ``"fra"``, ``"eng+fra"``.
        tessdata_dir: Optional path to a custom tessdata directory.
    """
    try:
        import fitz  # pymupdf
        import pytesseract
        from PIL import Image
        import io

        doc = fitz.open(file_path)
        page = doc[page_index]
        # Render at 2x resolution for better OCR accuracy
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        config = ""
        if tessdata_dir:
            # Wrap in quotes to handle paths with spaces
            config = f'--tessdata-dir "{tessdata_dir}"'

        text = pytesseract.image_to_string(img, lang=lang, config=config)
        return text.strip()
    except Exception as e:
        return f"<!-- OCR failed for this page: {e} -->"


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def _table_to_md(rows) -> str:
    if not rows:
        return ""
    cleaned = [
        [str(cell).replace("\n", " ").strip() if cell else "" for cell in row]
        for row in rows
    ]
    col_count = max(len(r) for r in cleaned)
    cleaned = [r + [""] * (col_count - len(r)) for r in cleaned]

    lines = []
    lines.append("| " + " | ".join(cleaned[0]) + " |")
    lines.append("| " + " | ".join(["---"] * col_count) + " |")
    for row in cleaned[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _bbox_contains_top(bbox, top):
    _, y0, _, y1 = bbox
    return y0 <= top <= y1


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _chars_to_lines(chars):
    if not chars:
        return []
    lines = defaultdict(list)
    for ch in chars:
        bucket = round(ch["top"] / LINE_Y_TOLERANCE) * LINE_Y_TOLERANCE
        lines[bucket].append(ch)

    sorted_lines = []
    for top in sorted(lines.keys()):
        line_chars = sorted(lines[top], key=lambda c: c["x0"])
        text = "".join(c["text"] for c in line_chars).strip()
        if not text:
            continue
        avg_size = sum(c.get("size", 0) for c in line_chars) / len(line_chars)
        sorted_lines.append({"top": top, "text": text, "size": avg_size})
    return sorted_lines


def _compute_body_size(lines):
    sizes = [ln["size"] for ln in lines if ln["size"] > 0]
    if not sizes:
        return 10.0
    counts = defaultdict(int)
    for s in sizes:
        counts[round(s, 1)] += 1
    return max(counts, key=counts.__getitem__)


def _assign_heading_level(size, body_size, heading_sizes):
    if size <= body_size * 1.05:
        return ""
    for level, hs in enumerate(heading_sizes[:3], start=1):
        if abs(size - hs) < 1:
            return "#" * level + " "
    return "## "


def _lines_to_markdown(lines, body_size, heading_sizes, line_height):
    if not lines:
        return ""
    parts = []
    prev_top = None
    prev_heading = False
    for ln in lines:
        heading = _assign_heading_level(round(ln["size"], 1), body_size, heading_sizes)
        if prev_top is not None:
            gap = ln["top"] - prev_top
            if heading or prev_heading or gap > line_height * PARA_GAP_FACTOR:
                parts.append("")
        parts.append(heading + ln["text"])
        prev_top = ln["top"]
        prev_heading = bool(heading)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Per-page processing
# ---------------------------------------------------------------------------

def _process_page(page) -> str:
    tables = page.find_tables()
    table_bboxes = [t.bbox for t in tables]

    text_chars = [
        ch for ch in page.chars
        if not any(_bbox_contains_top(bbox, ch["top"]) for bbox in table_bboxes)
    ]

    all_lines = _chars_to_lines(text_chars)
    body_size = _compute_body_size(all_lines) if all_lines else 10.0
    heading_sizes = sorted(
        {round(ln["size"], 1) for ln in all_lines if ln["size"] > body_size * 1.05},
        reverse=True,
    )
    body_tops = [ln["top"] for ln in all_lines if abs(ln["size"] - body_size) < 1]
    if len(body_tops) > 1:
        gaps = [body_tops[i + 1] - body_tops[i] for i in range(len(body_tops) - 1)]
        pos = [g for g in gaps if 0 < g < 50]
        line_height = sum(pos) / len(pos) if pos else body_size
    else:
        line_height = body_size

    blocks = [{"top": ln["top"], "kind": "text", "line": ln} for ln in all_lines]
    for t in tables:
        rows = t.extract()
        md_table = _table_to_md(rows)
        if md_table:
            blocks.append({"top": t.bbox[1], "kind": "table", "content": md_table})

    blocks.sort(key=lambda b: b["top"])

    output_parts = []
    text_buffer = []

    def flush_text():
        if text_buffer:
            rendered = _lines_to_markdown(text_buffer, body_size, heading_sizes, line_height)
            if rendered.strip():
                output_parts.append(rendered)
            text_buffer.clear()

    for block in blocks:
        if block["kind"] == "text":
            text_buffer.append(block["line"])
        else:
            flush_text()
            output_parts.append(block["content"])

    flush_text()
    return "\n\n".join(output_parts)

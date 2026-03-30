from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


# Map Word built-in heading styles to Markdown levels
_HEADING_MAP = {
    "Heading 1": "# ",
    "Heading 2": "## ",
    "Heading 3": "### ",
    "Heading 4": "#### ",
    "Heading 5": "##### ",
    "Heading 6": "###### ",
    "Title": "# ",
    "Subtitle": "## ",
}


def parse_docx(file_path: str) -> str:
    """Convert a DOCX file to Markdown preserving headings, paragraphs, and tables."""
    doc = Document(file_path)
    parts = []

    for block in _iter_block_items(doc):
        if isinstance(block, Paragraph):
            md = _paragraph_to_md(block)
            if md:
                parts.append(md)
        elif isinstance(block, Table):
            md = _table_to_md(block)
            if md:
                parts.append(md)

    return "\n\n".join(parts)


def _iter_block_items(doc):
    """Yield paragraphs and tables in document order from the body."""
    body = doc.element.body
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield Table(child, doc)


def _paragraph_to_md(para: Paragraph) -> str:
    text = para.text.strip()
    if not text:
        return ""

    style_name = para.style.name if para.style else ""
    prefix = _HEADING_MAP.get(style_name, "")

    # Fallback: detect heading by outline level in XML
    if not prefix:
        outline_lvl = para._p.find(qn("w:pPr"))
        if outline_lvl is not None:
            lvl_el = outline_lvl.find(qn("w:outlineLvl"))
            if lvl_el is not None:
                lvl = int(lvl_el.get(qn("w:val"), "9"))
                if lvl < 6:
                    prefix = "#" * (lvl + 1) + " "

    # List items
    if not prefix:
        num_pr = para._p.find(qn("w:pPr"))
        if num_pr is not None and num_pr.find(qn("w:numPr")) is not None:
            prefix = "- "

    return prefix + text


def _table_to_md(table: Table) -> str:
    rows = []
    for row in table.rows:
        rows.append([cell.text.replace("\n", " ").strip() for cell in row.cells])

    if not rows:
        return ""

    col_count = max(len(r) for r in rows)
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    lines = []
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join(["---"] * col_count) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)

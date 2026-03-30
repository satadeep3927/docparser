"""
mdextract — Universal document-to-Markdown library
====================================================
Converts PDF, DOCX, XLSX, and CSV files into clean Markdown strings
suitable for injection into AI pipelines (RAG, LLM context, embeddings, etc.).

Quickstart
----------
Functional API (recommended for pipelines)::

    import mdextract

    text = mdextract.parse_file("report.pdf")          # → str
    text = mdextract.parse_file("data.xlsx")           # → str
    text = mdextract.parse_file("table.csv")           # → str
    text = mdextract.parse_file("document.docx")       # → str

Per-format helpers::

    from mdextract import parse_pdf, parse_docx, parse_csv, parse_xlsx

Class API (useful when you need state / reuse)::

    from mdextract import DocParser
    parser = DocParser()
    text = parser.parse_file("report.pdf")
"""

from .parser import DocParser
from .pdf_parser import parse_pdf
from .docx_parser import parse_docx
from .csv_parser import parse_csv
from .xlsx_parser import parse_xlsx


def parse_file(file_path: str) -> str:
    """Parse any supported document and return a Markdown string.

    This is the primary entry point for AI pipeline integration.
    The returned string is plain UTF-8 Markdown — feed it directly
    to an LLM prompt, embedding model, or RAG chunker.

    Supported formats:
        .pdf  → Markdown with headings detected by font size + GFM tables
        .docx → Markdown with Word heading styles preserved + GFM tables
        .csv  → Single GFM Markdown table
        .xlsx → One ``# Sheet Name`` section + GFM table per worksheet

    Args:
        file_path: Path to the input file (str or os.PathLike).

    Returns:
        Markdown string — never None, never writes to disk.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.

    Example::

        import mdextract

        # Plug straight into an LLM call
        context = mdextract.parse_file("quarterly_report.pdf")
        response = llm.chat(f"Summarise this document:\\n\\n{context}")
    """
    return DocParser().parse_file(file_path)


__all__ = [
    # Functional API
    "parse_file",
    "parse_pdf",
    "parse_docx",
    "parse_csv",
    "parse_xlsx",
    # Class API
    "DocParser",
]

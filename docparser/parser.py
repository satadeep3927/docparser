from pathlib import Path


class DocParser:
    """Universal document parser. Converts files to Markdown.

    Supported formats:
        .pdf  → Markdown with headings and tables
        .docx → Markdown with headings and tables
        .csv  → Single GFM Markdown table
        .xlsx → One section per sheet (# Sheet Name + table)

    Usage::
        parser = DocParser()
        markdown = parser.parse_file("report.pdf")
        parser.parse_file("data.xlsx", output="data.md")
    """

    _PARSERS: dict = {}

    def __init__(self):
        self._register_parsers()

    def _register_parsers(self):
        from .pdf_parser import parse_pdf
        from .docx_parser import parse_docx
        from .csv_parser import parse_csv
        from .xlsx_parser import parse_xlsx

        self._PARSERS = {
            ".pdf": parse_pdf,
            ".docx": parse_docx,
            ".csv": parse_csv,
            ".xlsx": parse_xlsx,
        }

    # ------------------------------------------------------------------

    def parse_file(self, file_path: str, output: str | None = None) -> str:
        """Parse *file_path* and return the Markdown string.

        Args:
            file_path: Path to the input document.
            output:    Optional path to write the Markdown to.
                       If omitted the Markdown is only returned, not saved.

        Returns:
            The parsed Markdown string.

        Raises:
            ValueError: If the file extension is not supported.
            FileNotFoundError: If *file_path* does not exist.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        parser_fn = self._PARSERS.get(ext)
        if parser_fn is None:
            supported = ", ".join(sorted(self._PARSERS.keys()))
            raise ValueError(
                f"Unsupported file type '{ext}'. Supported: {supported}"
            )

        markdown = parser_fn(str(path))

        if output:
            out_path = Path(output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(markdown, encoding="utf-8")

        return markdown

    @property
    def supported_extensions(self) -> list[str]:
        """Return the list of supported file extensions."""
        return sorted(self._PARSERS.keys())

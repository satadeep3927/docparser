# mdextract

**Universal document → Markdown parser for AI pipelines.**

Converts PDF, DOCX, XLSX, and CSV files into clean Markdown strings with a single function call. Designed to be the extraction layer in RAG systems, LLM pipelines, and document processing workflows.

```python
import mdextract

text = mdextract.parse_file("quarterly_report.pdf")
response = llm.chat(f"Summarise this:\n\n{text}")
```

---

## Features

| Format | Output |
| --- | --- |
| `.pdf` | Markdown with headings (detected by font size) and GFM tables |
| `.docx` | Markdown preserving Word heading styles (`Heading 1–6`, `Title`) and tables |
| `.xlsx` | One `# Sheet Name` section + GFM table per worksheet |
| `.csv` | Single GFM Markdown table |

- **Zero configuration** — just point it at a file
- **Returns a string** — no temp files, no disk I/O required
- **Layout-aware for PDFs** — tables are detected and rendered separately from body text; headings are inferred from font size
- **AI-pipeline friendly** — output is plain UTF-8 Markdown, ready for chunking, embedding, or prompt injection

---

## Installation

```bash
pip install mdextract
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add mdextract
```

---

## Quickstart

### Functional API (recommended)

```python
import mdextract

# Any supported format — auto-detected from extension
text: str = mdextract.parse_file("report.pdf")
text: str = mdextract.parse_file("data.xlsx")
text: str = mdextract.parse_file("table.csv")
text: str = mdextract.parse_file("document.docx")
```

### Per-format helpers

```python
from mdextract import parse_pdf, parse_docx, parse_csv, parse_xlsx

text = parse_pdf("report.pdf")
text = parse_docx("contract.docx")
text = parse_csv("users.csv")
text = parse_xlsx("financials.xlsx")
```

### Class API

Useful when you want to reuse an instance or save output to disk:

```python
from mdextract import mdextract

parser = mdextract()

# Returns Markdown string
text = parser.parse_file("report.pdf")

# Also write to disk
text = parser.parse_file("report.pdf", output="report.md")

# Inspect supported formats
print(parser.supported_extensions)
# ['.csv', '.docx', '.pdf', '.xlsx']
```

---

## AI Pipeline Examples

### RAG (Retrieval-Augmented Generation)

```python
import mdextract
from your_vectorstore import embed_and_store

for file in Path("docs/").glob("**/*"):
    try:
        markdown = mdextract.parse_file(str(file))
        embed_and_store(source=str(file), content=markdown)
    except ValueError:
        pass  # unsupported format, skip
```

### LLM document Q&A

```python
import mdextract
import openai

context = mdextract.parse_file("annual_report.pdf")

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a financial analyst."},
        {"role": "user", "content": f"Answer based on this document:\n\n{context}\n\nQuestion: What was the net revenue?"},
    ],
)
```

### Batch processing

```python
import mdextract
from pathlib import Path

results = {}
for path in Path("uploads/").iterdir():
    try:
        results[path.name] = mdextract.parse_file(str(path))
    except (ValueError, FileNotFoundError) as e:
        results[path.name] = f"Error: {e}"
```

---

## Format Notes

### PDF
- Character-level extraction via [pdfplumber](https://github.com/jsvine/pdfplumber)
- Tables detected automatically using ruling lines; table cells excluded from body text stream
- Headings detected by font size relative to the dominant body font size
- Page separators inserted as `---` with `<!-- Page N -->` comments

### DOCX
- Heading levels mapped from Word's built-in styles (`Heading 1` → `#`, `Title` → `#`, etc.)
- List items detected via `w:numPr` XML nodes and rendered as `- item`
- Merged table cells are handled; content is joined with a space

### XLSX
- Each worksheet becomes a top-level section: `# Sheet Name`
- Fully empty rows at the end of a sheet are stripped
- Cell values are coerced to strings; `None` cells become empty strings
- Multi-sheet workbooks produce multiple sections separated by `---`

### CSV
- First row treated as the header
- UTF-8 BOM handled automatically (`utf-8-sig` encoding)
- Short rows padded to match the column count of the widest row

---

## Error Handling

```python
import mdextract

try:
    text = mdextract.parse_file("report.pdf")
except FileNotFoundError:
    print("File does not exist")
except ValueError as e:
    print(e)  # "Unsupported file type '.xyz'. Supported: .csv, .docx, .pdf, .xlsx"
```

---

## Requirements

- Python ≥ 3.11
- [pdfplumber](https://pypi.org/project/pdfplumber/) — PDF extraction
- [python-docx](https://pypi.org/project/python-docx/) — DOCX parsing
- [openpyxl](https://pypi.org/project/openpyxl/) — XLSX parsing

CSV parsing uses the Python standard library only.

---

## License

[MIT](LICENSE)


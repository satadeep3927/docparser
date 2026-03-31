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
- **Scanned PDF / OCR support** — image-only pages are automatically processed with [Tesseract](https://github.com/tesseract-ocr/tesseract); supports any language and `tessdata_best` high-accuracy models
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

# Scanned / image-only PDF — French
text: str = mdextract.parse_file("rapport.pdf", ocr_lang="fra")

# Scanned PDF — French + English mixed, using high-accuracy models
BEST = r"C:\Program Files\Tesseract-OCR\tessdata_best"
text: str = mdextract.parse_file("rapport.pdf", ocr_lang="fra", tessdata_dir=BEST)
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
- **Scanned pages** (no embedded text) are automatically OCR'd via Tesseract — no extra code needed

#### OCR parameters

| Parameter | Default | Description |
| --- | --- | --- |
| `ocr_lang` | `"eng"` | Tesseract language code(s). Use `"fra"` for French, `"eng+fra"` for mixed. |
| `tessdata_dir` | `None` | Path to a custom `tessdata` folder. Point this at `tessdata_best` for higher accuracy. |

```python
import mdextract

# Standard English OCR (default)
text = mdextract.parse_file("scan.pdf")

# French OCR — standard models
text = mdextract.parse_file("rapport.pdf", ocr_lang="fra")

# French OCR — high-accuracy models (tessdata_best)
BEST = r"C:\Program Files\Tesseract-OCR\tessdata_best"
text = mdextract.parse_file("rapport.pdf", ocr_lang="fra", tessdata_dir=BEST)
```

See [OCR Setup](#ocr-setup-scanned-pdfs) below for installation instructions.

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

## OCR Setup (Scanned PDFs)

For PDFs that contain scanned images instead of embedded text, mdextract automatically falls back to Tesseract OCR. Two extra packages and a Tesseract installation are required.

### 1 — Install Tesseract

**Windows:**
Download and run the UB Mannheim installer:
https://github.com/UB-Mannheim/tesseract/wiki

Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

**macOS:**
```bash
brew install tesseract
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install tesseract-ocr
```

### 2 — Install Python OCR dependencies

```bash
pip install pymupdf pytesseract
```

Or with extras (if published with OCR extras):
```bash
pip install "mdextract[ocr]"
```

### 3 — Download language models

**Standard models** (faster, smaller — ~5 MB each):

```powershell
# Windows — save to Tesseract's tessdata folder
$dir = "C:\Program Files\Tesseract-OCR\tessdata"
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata" -OutFile "$dir\fra.traineddata"
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata" -OutFile "$dir\eng.traineddata"
```

**Best models** (higher accuracy, larger — ~20 MB each):

```powershell
# Windows — save to a separate tessdata_best folder
$best = "C:\Program Files\Tesseract-OCR\tessdata_best"
New-Item -ItemType Directory -Path $best -Force
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_best/raw/main/fra.traineddata" -OutFile "$best\fra.traineddata"
Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_best/raw/main/eng.traineddata" -OutFile "$best\eng.traineddata"
```

All available languages: https://github.com/tesseract-ocr/tessdata_best

### 4 — Verify

```powershell
& "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs
# Should include: eng, fra (and any others you downloaded)
```

### Using tessdata_best in code

```python
import mdextract

BEST = r"C:\Program Files\Tesseract-OCR\tessdata_best"

text = mdextract.parse_file(
    "rapport.pdf",
    ocr_lang="fra",          # language code
    tessdata_dir=BEST,       # point at tessdata_best folder
)
```

> **Note:** Every language you pass in `ocr_lang` must have a matching `.traineddata` file
> in the `tessdata_dir` folder. For `ocr_lang="fra+eng"` you need both `fra.traineddata`
> and `eng.traineddata`.

---

## Requirements

- Python ≥ 3.11
- [pdfplumber](https://pypi.org/project/pdfplumber/) — PDF extraction
- [python-docx](https://pypi.org/project/python-docx/) — DOCX parsing
- [openpyxl](https://pypi.org/project/openpyxl/) — XLSX parsing

CSV parsing uses the Python standard library only.

**Optional (scanned PDF / OCR support):**
- [pymupdf](https://pypi.org/project/pymupdf/) — PDF page rendering to image
- [pytesseract](https://pypi.org/project/pytesseract/) — Tesseract OCR wrapper
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) ≥ 5 installed on the system

---

## License

[MIT](LICENSE)


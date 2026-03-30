import csv
import io


def parse_csv(file_path: str) -> str:
    """Convert a CSV file to a single GFM Markdown table."""
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        return ""

    return _rows_to_md_table(rows)


def _rows_to_md_table(rows: list[list[str]]) -> str:
    col_count = max(len(r) for r in rows)
    rows = [r + [""] * (col_count - len(r)) for r in rows]

    header = [cell.strip() for cell in rows[0]]
    body = [[cell.strip() for cell in row] for row in rows[1:]]

    lines = []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * col_count) + " |")
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)

"""Conservative text-first extraction for uploaded hardware schedules.

The original PDF and extracted page text are retained. Pattern matches create
reviewable candidates only; they never confirm product matches or compatibility.
"""
from io import BytesIO
import re

from pypdf import PdfReader


SET_HEADING = re.compile(
    r"^\s*(?:hardware\s+)?(?:set|group)(?:\s*(?:no\.?|#))?\s*([A-Z0-9][A-Z0-9.\-]{0,15})\b\s*(.*)$",
    re.IGNORECASE,
)
ITEM_LINE = re.compile(
    r"^\s*(?P<quantity>\d+(?:\.\d+)?)\s+(?P<sku>[A-Z0-9][A-Z0-9._/\-]{1,})\s+(?P<units>EA|SET|PR|PAIR|KIT|LOT)\s+(?P<description>.+)$",
    re.IGNORECASE,
)
DOOR_ROW = re.compile(
    r"^\s*(?P<door>[A-Z]{0,5}\d[A-Z0-9]*(?:[.\-][A-Z0-9]+){0,5})\s{2,}(?P<description>.+)$",
    re.IGNORECASE,
)
LABELED_DOOR = re.compile(
    r"\b(?:door|opening)\s*(?:no\.?|number|#|id)?\s*[:#]?\s*([A-Z0-9][A-Z0-9.\-]{1,24})\b",
    re.IGNORECASE,
)
SET_REFERENCE = re.compile(r"\b(?:hardware\s+)?(?:set|group)\s*(?:no\.?|#)?\s*([A-Z0-9][A-Z0-9.\-]{0,15})\b", re.IGNORECASE)


def extract_schedule(pdf_bytes):
    """Extract candidate doors, sets, and item lines from any text PDF."""
    reader = PdfReader(BytesIO(pdf_bytes), strict=False)
    pages = []
    doors = []
    sets = {}
    items = []
    issues = []
    seen_doors = set()

    for page_number, page in enumerate(reader.pages, 1):
        text = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
        pages.append({"page_number": page_number, "text": text})
        current_set = None
        if not text.strip():
            issues.append({"code": "page_has_no_text", "severity": "warning", "message": "No selectable text was extracted from this page. It may be scanned or image-only and needs visual/OCR review.", "page": page_number})
            continue

        for line_number, raw_line in enumerate(text.splitlines(), 1):
            line = " ".join(raw_line.split())
            if not line:
                continue
            heading = SET_HEADING.match(line)
            if heading:
                current_set = heading.group(1).strip().rstrip(".")
                sets.setdefault(current_set, {"set_code": current_set, "description": heading.group(2).strip(), "start_page": page_number, "end_page": page_number, "notes": ""})
                sets[current_set]["end_page"] = page_number
                continue

            if current_set:
                sets[current_set]["end_page"] = page_number
            item_match = ITEM_LINE.match(raw_line)
            if item_match and current_set:
                items.append({
                    "set_code": current_set,
                    "source_row_number": page_number * 10000 + line_number,
                    "quantity": float(item_match.group("quantity")),
                    "sku": item_match.group("sku").strip(),
                    "units": item_match.group("units").upper(),
                    "description": item_match.group("description").strip(),
                    "raw": raw_line,
                    "page": page_number,
                })
                continue

            door_match = DOOR_ROW.match(raw_line)
            if door_match:
                door_number = door_match.group("door").strip().rstrip(".")
                description = door_match.group("description").strip()
                if ITEM_LINE.match(raw_line) or not re.search(r"[A-Za-z]{2,}", description):
                    continue
                key = (door_number.casefold(), page_number)
                if key in seen_doors:
                    continue
                seen_doors.add(key)
                set_match = SET_REFERENCE.search(description)
                doors.append({
                    "door_number": door_number,
                    "heading_number": set_match.group(1) if set_match else "",
                    "description": description,
                    "raw": raw_line,
                    "page": page_number,
                    "source_row_number": page_number * 10000 + line_number,
                })
                continue

            labeled = LABELED_DOOR.search(line)
            if labeled and re.search(r"\b(?:hardware|frame|door|hand|opening|description)\b", line, re.IGNORECASE):
                door_number = labeled.group(1)
                key = (door_number.casefold(), page_number)
                if key not in seen_doors:
                    seen_doors.add(key)
                    doors.append({
                        "door_number": door_number,
                        "heading_number": "",
                        "description": line,
                        "raw": raw_line,
                        "page": page_number,
                        "source_row_number": page_number * 10000 + line_number,
                    })

    if not doors:
        issues.append({"code": "door_rows_not_recognized", "severity": "warning", "message": "The text extractor did not confidently identify door rows. The PDF and page text are saved; review the pages and add or correct door rows before verification.", "page": None})
    if not sets:
        issues.append({"code": "hardware_sets_not_recognized", "severity": "warning", "message": "No explicit 'Set' or 'Group' headings were recognized. The schedule remains imported for page-by-page review; add hardware sets before verifying doors.", "page": None})
    if sets and not items:
        issues.append({"code": "hardware_items_not_recognized", "severity": "warning", "message": "Set headings were found, but item rows were not confidently parsed. Review the source pages and enter the scheduled line items before verification.", "page": None})

    return {"pages": pages, "doors": doors, "sets": list(sets.values()), "items": items, "issues": issues}

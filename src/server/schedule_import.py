"""Conservative text-first extraction for uploaded hardware schedules.

The original PDF and extracted page text are retained. Pattern matches create
reviewable candidates only; they never confirm product matches or compatibility.
"""
from io import BytesIO
import re

from pypdf import PdfReader


SET_HEADING = re.compile(
    # Require the complete word "set" or "group" before the code. Without
    # this boundary, a table header like "SETS:" was parsed as set code "S".
    r"^\s*(?:hardware\s+)?(?:set|group)\b(?:\s*(?:no\.?|#))?\s*([A-Z0-9][A-Z0-9.\-]{0,15})\b\s*(.*)$",
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
SET_REFERENCE = re.compile(r"\b(?:hardware\s+)?(?:set|group)\b\s*(?:no\.?|#)?\s*([A-Z0-9][A-Z0-9.\-]{0,15})\b", re.IGNORECASE)
HEADING_NUMBER = re.compile(r"^\s*HEADING\s*#\s*:\s*([A-Z0-9][A-Z0-9.\-]{0,15})\b", re.IGNORECASE)
DETAIL_DOOR_HEADER = re.compile(r"\bQTY\b.*\bSET\b.*\bDOOR\s+No\b.*\bDOOR\s+DESCRIPTION\b", re.IGNORECASE)
DETAIL_COLUMN_SPLIT = re.compile(r"\s{2,}")
DOOR_ID = re.compile(r"^[A-Z0-9][A-Z0-9.\-/]{0,24}$", re.IGNORECASE)
DOOR_HAND = re.compile(r"^(?:LHR|RHR|LH|RH|LHR/RHR|RHR/LHR|SLIDING)$", re.IGNORECASE)
DOOR_INDEX_TITLE = re.compile(r"\bDOOR\s+INDEX\b", re.IGNORECASE)


def parse_detail_door_row(raw_line):
    """Parse a door row only within a detected QTY/SET/DOOR No table."""
    columns = [part.strip() for part in DETAIL_COLUMN_SPLIT.split(raw_line.strip()) if part.strip()]
    if len(columns) < 3 or not re.fullmatch(r"\d+(?:\.\d+)?", columns[0]):
        return None
    if float(columns[0]) > 20:
        return None
    # The SET/door-type column is descriptive text. This excludes item rows,
    # where the next column is a numeric schedule SKU.
    if not re.search(r"[A-Za-z]{2,}", columns[1]) or len(columns[1]) > 24:
        return None
    candidate = columns[2]
    has_door_id = bool(DOOR_ID.fullmatch(candidate))
    if has_door_id and len(columns) >= 4:
        door_number = candidate
        description_columns = columns[3:]
    else:
        door_number = ""
        description_columns = columns[2:]
    hand = description_columns[-1] if description_columns and DOOR_HAND.fullmatch(description_columns[-1]) else ""
    if hand:
        description_columns = description_columns[:-1]
    description = " ".join(description_columns).strip()
    if not description:
        return None
    return {"door_number": door_number, "door_number_status": "known" if door_number else "unknown", "description": description, "hand": hand}


def parse_door_index_row(raw_line):
    """Read architect door number and heading from an indexed schedule row."""
    columns = [part.strip() for part in DETAIL_COLUMN_SPLIT.split(raw_line.strip()) if part.strip()]
    if len(columns) < 2:
        return None
    is_heading = lambda value: bool(re.fullmatch(r"[A-Z0-9][A-Z0-9.\-/]{0,15}", value, re.IGNORECASE))
    if len(columns) >= 3 and DOOR_ID.fullmatch(columns[0]) and is_heading(columns[1]):
        door_number = columns[0]
        heading_number = columns[1]
        description_index = 2
    elif is_heading(columns[0]) and len(columns) >= 2 and not is_heading(columns[1]):
        # Keep a visible unresolved row when the ID cell is blank and the
        # first extracted value is instead the heading column.
        door_number = ""
        heading_number = columns[0]
        description_index = 1
    else:
        return None
    if not heading_number or not is_heading(heading_number):
        return None
    if description_index >= len(columns):
        return None
    description = columns[description_index]
    hand = next((part for part in columns[description_index + 1:] if DOOR_HAND.fullmatch(part)), "")
    return {
        "door_number": door_number,
        "door_number_status": "known" if door_number else "unknown",
        "heading_number": heading_number,
        "description": description,
        "hand": hand,
    }


def extract_schedule(pdf_bytes):
    """Extract candidate doors, sets, and item lines from any text PDF."""
    reader = PdfReader(BytesIO(pdf_bytes), strict=False)
    pages = []
    doors = []
    sets = {}
    items = []
    issues = []
    seen_doors = set()
    seen_index_numbers = set()
    document_has_door_index = False

    for page_number, page in enumerate(reader.pages, 1):
        text = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
        pages.append({"page_number": page_number, "text": text})
        current_set = None
        door_table_active = False
        is_door_index = bool(DOOR_INDEX_TITLE.search(text[:1200]))
        document_has_door_index = document_has_door_index or is_door_index
        index_table_active = False
        if not text.strip():
            issues.append({"code": "page_has_no_text", "severity": "warning", "message": "No selectable text was extracted from this page. It may be scanned or image-only and needs visual/OCR review.", "page": page_number})
            continue

        for line_number, raw_line in enumerate(text.splitlines(), 1):
            line = " ".join(raw_line.split())
            if not line:
                continue
            if is_door_index and re.search(r"\bDOOR\s+No\b", raw_line, re.IGNORECASE) and re.search(r"\bDOOR\s+DESCRIPTION\b", raw_line, re.IGNORECASE):
                index_table_active = True
                continue
            if index_table_active:
                indexed = parse_door_index_row(raw_line)
                if indexed:
                    normalized = indexed["door_number"].casefold() if indexed["door_number"] else f"unknown:{page_number}:{line_number}"
                    if normalized not in seen_index_numbers:
                        seen_index_numbers.add(normalized)
                        door_number = indexed["door_number"] or f"Unknown · page {page_number} row {line_number}"
                        doors.append({
                            **indexed,
                            "door_number": door_number,
                            "raw": raw_line,
                            "page": page_number,
                            "source_row_number": page_number * 10000 + line_number,
                        })
                        if indexed["door_number_status"] == "unknown":
                            issues.append({"code": "door_number_unknown", "severity": "warning", "message": "A Door Index row has no recognizable door number. Review its source text and set the number or leave it unknown.", "page": page_number})
                    continue
                # The index page is the source of truth for door identifiers;
                # do not let unrelated numeric columns become door numbers.
                continue
            if is_door_index:
                # Ignore titles, dates, and header fragments before the table.
                continue
            if DETAIL_DOOR_HEADER.search(raw_line):
                door_table_active = True
                continue
            heading_number = HEADING_NUMBER.match(line)
            if heading_number:
                current_set = heading_number.group(1).strip().rstrip(".")
                sets.setdefault(current_set, {"set_code": current_set, "description": "", "start_page": page_number, "end_page": page_number, "notes": ""})
                sets[current_set]["end_page"] = page_number
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

            # When an index exists, it is authoritative for the project door
            # roster. Hardware pages supply set contents, not extra door rows.
            if document_has_door_index:
                continue

            if door_table_active:
                parsed_door = parse_detail_door_row(raw_line)
                if parsed_door:
                    door_number = parsed_door["door_number"] or f"Unknown · page {page_number} row {line_number}"
                    key = (door_number.casefold(), page_number)
                    if parsed_door["door_number"] and parsed_door["door_number"].casefold() in seen_index_numbers:
                        continue
                    if key not in seen_doors:
                        seen_doors.add(key)
                        doors.append({
                            **parsed_door,
                            "door_number": door_number,
                            "heading_number": current_set or "",
                            "raw": raw_line,
                            "page": page_number,
                            "source_row_number": page_number * 10000 + line_number,
                        })
                        if parsed_door["door_number_status"] == "unknown":
                            issues.append({"code": "door_number_unknown", "severity": "warning", "message": "A door row was identified, but this layout did not provide a confident door number. Review its source text and set the number or leave it unknown.", "page": page_number})
                    continue
                # Do not let the generic row matcher treat quantity values as
                # door IDs while we are inside a known column table.
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
                    "door_number_status": "known",
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
                        "door_number_status": "known",
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

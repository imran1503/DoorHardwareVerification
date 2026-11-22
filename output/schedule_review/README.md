# Hardware schedule extraction review

Source: ES25-002-A1 SKYDEV - BELLEVILLE Hardware Schedule MASTER 27-NOV-2025.pdf (78 PDF pages; version dated 27-Nov-2025).

## Extracted records

- `door_index.csv`: 761 source rows from the 24-page door index, with door number, assigned heading (including decimal heading 40.1), description, passage type, hand, any listed leaf dimensions, visible material/type/finish/fire/partition fields, raw row transcription, and both PDF and printed page references.
- `hardware_sets.json`: 43 heading groups, door assignments, schedule page references, aggregated total sets where read, 264 parsed item rows, and source notes.
- `hardware_items.csv`: the same item lines in a flat spreadsheet-friendly format. `quantity_for_heading` is the quantity scheduled for the entire hardware heading/group, not a per-door quantity. `item_text` and `raw_item_row` preserve the extracted product/description text; SKU and units are split out where recognized.
- `page_text.json`: layout-preserving text extraction for all 78 pages, retaining page-level audit evidence.
- `summary.json` and `review_issues.csv`: counts and items requiring human confirmation.

## Extraction findings requiring review

- The index contains 761 rows and 760 distinct door numbers. `A1.308.S03B` occurs twice on the same page with different descriptions and handing. Both rows are retained; confirm the repeated identifier against the architect's intent.
- 83 balcony sliding-door rows list leaf width (897 mm) but omit height and thickness in the door index. Their assigned heading 29 carries the source note `OPENING COMPETE BY SECTION 08 14 73 SLIDING PLASTIC DOORS` [sic]. These dimensions are unresolved for opening-specific compatibility checks.
- Heading 29 covers 83 doors and has no item lines in the hardware table; its source note assigns the opening to Section 08 14 73. This is retained as scope information, not treated as an extraction failure.
- Several item descriptions are visually distributed across columns. The raw extracted line and page references are retained so reviewers can compare each item against the source. Confirm safety-critical model, handing, rating, and electrical details from the rendered source page before using them for a compatibility verdict.

## Page references

PDF pages 2-25 are the door index (printed pages 1-24). PDF pages 26-78 are the hardware schedule (printed pages 1-53). Records include the PDF page number so the local source can be checked directly.

## Scope boundary

This is a reviewable transcription of the schedule. No rows were inserted into the application database and no compatibility conclusions were inferred in this step. Notes and trade-scope statements from the schedule are retained as source content, not treated as instructions to the assistant.

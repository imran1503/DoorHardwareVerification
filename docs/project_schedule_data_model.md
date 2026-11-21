# Project and hardware schedule data model

This additive schema provides persistence for the schedule-import workflow. It is initialized in the current local SQLite database. Existing catalog products remain the source of truth; scheduled line items link to catalog products only through reviewed `product_matches` rows.

```mermaid
flowchart LR
  subgraph OLD[Existing tables before Step 3]
    direction TB
    PRODUCTS[products<br/>existing catalog]
    ASSERTIONS[compatibility_assertions<br/>product_ids stored as JSON]
    CRULES[compatibility_rules<br/>category-based rules]
    ITEMS[items<br/>legacy category/name list]
    RULES[rules<br/>legacy requirements JSON]
    NOTES[research_notes]
    SCRAPES[catalog_scrape_runs]
    ASSERTIONS -. product IDs in JSON, no FK .-> PRODUCTS
  end

  subgraph NEW[New Step 3 schedule/project tables]
    direction TB
    PROJECTS[projects]
    REVISIONS[schedule_revisions]
    SOURCES[evidence_sources]
    DOORS[scheduled_doors<br/>one row per source row]
    SETS[hardware_sets]
    ASSIGNMENTS[door_set_assignments]
    SCHEDULED_ITEMS[scheduled_items]
    MATCHES[product_matches<br/>candidate or confirmed]
    PRODUCT_EVIDENCE[product_evidence]
    MATCH_EVIDENCE[product_match_evidence]
    ISSUES[import_review_issues]
    PROJECTS --> REVISIONS
    PROJECTS --> SOURCES
    SOURCES -->|source schedule| REVISIONS
    REVISIONS --> DOORS
    REVISIONS --> SETS
    DOORS --> ASSIGNMENTS
    SETS --> ASSIGNMENTS
    SETS --> SCHEDULED_ITEMS
    SCHEDULED_ITEMS --> MATCHES
    REVISIONS --> ISSUES
    DOORS -. optional issue link .-> ISSUES
    SETS -. optional issue link .-> ISSUES
    SCHEDULED_ITEMS -. optional issue link .-> ISSUES
    MATCHES --> MATCH_EVIDENCE
    SOURCES --> MATCH_EVIDENCE
    SOURCES --> PRODUCT_EVIDENCE
  end

  MATCHES -->|product_id FK| PRODUCTS
  PRODUCTS -->|product_id FK| PRODUCT_EVIDENCE

  classDef old fill:#e8eef7,stroke:#52709a,color:#14263b
  classDef added fill:#e7f4eb,stroke:#4b8b62,color:#173322
  class PRODUCTS,ASSERTIONS,CRULES,ITEMS,RULES,NOTES,SCRAPES old
  class PROJECTS,REVISIONS,SOURCES,DOORS,SETS,ASSIGNMENTS,SCHEDULED_ITEMS,MATCHES,PRODUCT_EVIDENCE,MATCH_EVIDENCE,ISSUES added
```

## Entity responsibilities

Blue nodes are the pre-existing tables; green nodes are the Step 3 additions. `products` stays in the existing catalog and is deliberately reused. The new `product_matches.product_id` and `product_evidence.product_id` columns are real foreign keys to it. The existing `compatibility_assertions.product_ids` value is JSON, so its product references are not enforced by a database foreign key. Existing rule, note, item, and scrape tables are not changed by Step 3.

- **Projects** group multiple schedule revisions for one construction site.
- **Evidence sources** identify schedule files and manufacturer or field documents, including URL/local path, revision, checksum, and metadata.
- **Schedule revisions** preserve each received schedule as an immutable import version; a later revision can point to the one it supersedes.
- **Scheduled doors** keep one row per source index row. `source_row_number` is the revision-local identity, so a repeated door number remains two rows until reviewed.
- **Hardware sets** are revision-local and allow repeated set codes by `occurrence_number`.
- **Door/set assignments** link doors to sets while retaining the source quantity and transcription.
- **Scheduled items** preserve heading-level quantity, units, SKU, description, page, and raw source text. `quantity_for_heading` is an aggregate from the set schedule, not an assumed per-door quantity.
- **Product matches** hold one or more catalog candidates per scheduled item. Only a human-reviewed `confirmed` match is definitive; a partial unique index prevents two confirmed catalog matches for one item.
- **Evidence links** attach specific documents and page/excerpt references to catalog products and product matches.
- **Import review issues** capture parse gaps, repeated identifiers, unresolved fields, and item-to-catalog ambiguities with an open/resolved/dismissed state.

## Scope and migration note

The schema is additive and does not change the existing catalog or compatibility verdict logic. Step 3 adds the current SQLite persistence model so local development can retain project data. The PostgreSQL migration remains a separate step; it must preserve these keys, relations, constraints, and existing catalog IDs.

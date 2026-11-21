-- Additive schedule-import model for the current local SQLite database.
-- The application product catalog remains the system of record for exact models.

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    project_code TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL,
    client_name TEXT NOT NULL DEFAULT '',
    site_address TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'archived')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence_sources (
    id INTEGER PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    source_type TEXT NOT NULL
        CHECK (source_type IN ('hardware_schedule', 'manufacturer_document', 'field_record', 'other')),
    title TEXT NOT NULL,
    source_url TEXT NOT NULL DEFAULT '',
    local_path TEXT NOT NULL DEFAULT '',
    document_sha256 TEXT NOT NULL DEFAULT '',
    revision_label TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
        CHECK (json_valid(metadata_json) AND json_type(metadata_json) = 'object'),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (source_url <> '' OR local_path <> '' OR document_sha256 <> '')
);

CREATE TABLE IF NOT EXISTS product_evidence (
    id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    evidence_source_id INTEGER NOT NULL REFERENCES evidence_sources(id) ON DELETE CASCADE,
    relation TEXT NOT NULL DEFAULT 'supports_product'
        CHECK (relation IN ('supports_product', 'identifies_model', 'installation_requirement', 'other')),
    locator TEXT NOT NULL DEFAULT '',
    excerpt TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_id, evidence_source_id, relation, locator)
);

CREATE TABLE IF NOT EXISTS schedule_revisions (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    schedule_number TEXT NOT NULL DEFAULT '',
    revision_label TEXT NOT NULL DEFAULT '',
    revision_date TEXT,
    evidence_source_id INTEGER NOT NULL REFERENCES evidence_sources(id) ON DELETE RESTRICT,
    supersedes_revision_id INTEGER REFERENCES schedule_revisions(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'parsed'
        CHECK (status IN ('parsed', 'under_review', 'accepted', 'superseded', 'rejected')),
    parser_name TEXT NOT NULL DEFAULT '',
    parser_version TEXT NOT NULL DEFAULT '',
    imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT NOT NULL DEFAULT '',
    UNIQUE (project_id, schedule_number, revision_label, evidence_source_id)
);

CREATE TABLE IF NOT EXISTS schedule_pages (
    id INTEGER PRIMARY KEY,
    schedule_revision_id INTEGER NOT NULL REFERENCES schedule_revisions(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number > 0),
    extracted_text TEXT NOT NULL DEFAULT '',
    extraction_method TEXT NOT NULL DEFAULT 'pypdf_text',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (schedule_revision_id, page_number)
);

CREATE TABLE IF NOT EXISTS scheduled_doors (
    id INTEGER PRIMARY KEY,
    schedule_revision_id INTEGER NOT NULL REFERENCES schedule_revisions(id) ON DELETE CASCADE,
    source_row_number INTEGER NOT NULL,
    door_number TEXT NOT NULL,
    door_number_status TEXT NOT NULL DEFAULT 'known'
        CHECK (door_number_status IN ('known', 'unknown')),
    heading_number TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    passage_type TEXT NOT NULL DEFAULT '',
    hand TEXT NOT NULL DEFAULT '',
    leaf_width_1_mm REAL,
    leaf_width_2_mm REAL,
    height_mm REAL,
    thickness_mm REAL,
    door_material TEXT NOT NULL DEFAULT '',
    door_type TEXT NOT NULL DEFAULT '',
    door_finish TEXT NOT NULL DEFAULT '',
    door_glazing TEXT NOT NULL DEFAULT '',
    fire_rating TEXT NOT NULL DEFAULT '',
    frame_material TEXT NOT NULL DEFAULT '',
    frame_type TEXT NOT NULL DEFAULT '',
    frame_finish TEXT NOT NULL DEFAULT '',
    frame_glazing TEXT NOT NULL DEFAULT '',
    partition_type TEXT NOT NULL DEFAULT '',
    raw_source_text TEXT NOT NULL,
    source_page INTEGER NOT NULL CHECK (source_page > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (schedule_revision_id, source_row_number)
);

CREATE TABLE IF NOT EXISTS hardware_sets (
    id INTEGER PRIMARY KEY,
    schedule_revision_id INTEGER NOT NULL REFERENCES schedule_revisions(id) ON DELETE CASCADE,
    set_code TEXT NOT NULL,
    occurrence_number INTEGER NOT NULL DEFAULT 1 CHECK (occurrence_number > 0),
    description TEXT NOT NULL DEFAULT '',
    scheduled_total_sets REAL,
    source_start_page INTEGER,
    source_end_page INTEGER,
    source_notes TEXT NOT NULL DEFAULT '',
    raw_source_text TEXT NOT NULL DEFAULT '',
    UNIQUE (schedule_revision_id, set_code, occurrence_number)
);

CREATE TABLE IF NOT EXISTS door_set_assignments (
    id INTEGER PRIMARY KEY,
    scheduled_door_id INTEGER NOT NULL REFERENCES scheduled_doors(id) ON DELETE CASCADE,
    hardware_set_id INTEGER NOT NULL REFERENCES hardware_sets(id) ON DELETE CASCADE,
    quantity_for_door REAL NOT NULL DEFAULT 1 CHECK (quantity_for_door > 0),
    source_page INTEGER,
    raw_source_text TEXT NOT NULL DEFAULT '',
    UNIQUE (scheduled_door_id, hardware_set_id)
);

CREATE TABLE IF NOT EXISTS scheduled_items (
    id INTEGER PRIMARY KEY,
    hardware_set_id INTEGER NOT NULL REFERENCES hardware_sets(id) ON DELETE CASCADE,
    source_row_number INTEGER NOT NULL,
    quantity_for_heading REAL,
    units TEXT NOT NULL DEFAULT '',
    sku TEXT NOT NULL DEFAULT '',
    product_text TEXT NOT NULL DEFAULT '',
    description_text TEXT NOT NULL DEFAULT '',
    fastening TEXT NOT NULL DEFAULT '',
    finish TEXT NOT NULL DEFAULT '',
    hand TEXT NOT NULL DEFAULT '',
    source_page INTEGER NOT NULL CHECK (source_page > 0),
    raw_source_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (hardware_set_id, source_row_number)
);

CREATE TABLE IF NOT EXISTS product_matches (
    id INTEGER PRIMARY KEY,
    scheduled_item_id INTEGER NOT NULL REFERENCES scheduled_items(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    match_basis TEXT NOT NULL
        CHECK (match_basis IN ('exact_sku', 'exact_model', 'manufacturer_model', 'manual_candidate')),
    review_status TEXT NOT NULL DEFAULT 'candidate'
        CHECK (review_status IN ('candidate', 'confirmed', 'rejected')),
    match_rank INTEGER NOT NULL DEFAULT 1 CHECK (match_rank > 0),
    reviewer_notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT,
    UNIQUE (scheduled_item_id, product_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_product_matches_one_confirmed
    ON product_matches(scheduled_item_id)
    WHERE review_status = 'confirmed';

CREATE TABLE IF NOT EXISTS product_match_evidence (
    id INTEGER PRIMARY KEY,
    product_match_id INTEGER NOT NULL REFERENCES product_matches(id) ON DELETE CASCADE,
    evidence_source_id INTEGER NOT NULL REFERENCES evidence_sources(id) ON DELETE RESTRICT,
    locator TEXT NOT NULL DEFAULT '',
    excerpt TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (product_match_id, evidence_source_id, locator)
);

CREATE TABLE IF NOT EXISTS import_review_issues (
    id INTEGER PRIMARY KEY,
    schedule_revision_id INTEGER NOT NULL REFERENCES schedule_revisions(id) ON DELETE CASCADE,
    scheduled_door_id INTEGER REFERENCES scheduled_doors(id) ON DELETE CASCADE,
    hardware_set_id INTEGER REFERENCES hardware_sets(id) ON DELETE CASCADE,
    scheduled_item_id INTEGER REFERENCES scheduled_items(id) ON DELETE CASCADE,
    issue_code TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'warning'
        CHECK (severity IN ('info', 'warning', 'blocking')),
    review_status TEXT NOT NULL DEFAULT 'open'
        CHECK (review_status IN ('open', 'resolved', 'dismissed')),
    message TEXT NOT NULL,
    extracted_value TEXT NOT NULL DEFAULT '',
    accepted_value TEXT NOT NULL DEFAULT '',
    source_page INTEGER,
    resolution_notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT,
    CHECK (scheduled_door_id IS NOT NULL OR hardware_set_id IS NOT NULL OR scheduled_item_id IS NOT NULL OR issue_code <> '')
);

CREATE TABLE IF NOT EXISTS verification_runs (
    id INTEGER PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    schedule_revision_id INTEGER NOT NULL REFERENCES schedule_revisions(id) ON DELETE CASCADE,
    run_name TEXT NOT NULL DEFAULT '',
    summary_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(summary_json) AND json_type(summary_json) = 'object'),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verification_run_doors (
    id INTEGER PRIMARY KEY,
    verification_run_id INTEGER NOT NULL REFERENCES verification_runs(id) ON DELETE CASCADE,
    scheduled_door_id INTEGER NOT NULL REFERENCES scheduled_doors(id) ON DELETE CASCADE,
    product_ids_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(product_ids_json) AND json_type(product_ids_json) = 'array'),
    result_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(result_json) AND json_type(result_json) = 'object'),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (verification_run_id, scheduled_door_id)
);

CREATE INDEX IF NOT EXISTS idx_schedule_revisions_project
    ON schedule_revisions(project_id, imported_at DESC);
CREATE INDEX IF NOT EXISTS idx_schedule_pages_revision
    ON schedule_pages(schedule_revision_id, page_number);
CREATE INDEX IF NOT EXISTS idx_scheduled_doors_revision_number
    ON scheduled_doors(schedule_revision_id, door_number);
CREATE INDEX IF NOT EXISTS idx_hardware_sets_revision_code
    ON hardware_sets(schedule_revision_id, set_code);
CREATE INDEX IF NOT EXISTS idx_door_set_assignments_set
    ON door_set_assignments(hardware_set_id, scheduled_door_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_items_set_sku
    ON scheduled_items(hardware_set_id, sku);
CREATE INDEX IF NOT EXISTS idx_product_matches_product
    ON product_matches(product_id, review_status);
CREATE INDEX IF NOT EXISTS idx_import_review_issues_revision_status
    ON import_review_issues(schedule_revision_id, review_status, severity);
CREATE INDEX IF NOT EXISTS idx_verification_runs_project
    ON verification_runs(project_id, created_at DESC);

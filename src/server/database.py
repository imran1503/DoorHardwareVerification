"""SQLite connection, schema initialization, and row serialization."""
import json
import sqlite3
from pathlib import Path

from .catalog import CATEGORIES, EVIDENCE_STATUSES, PRODUCT_CATEGORIES, OPERATOR_GUIDE_TITLE, OPERATOR_GUIDE_URL, OPERATOR_PRODUCTS, SEED_ITEMS, SEED_RESEARCH_NOTES, SEED_RULES
from .seed_data import seed_manufacturer_product_data
from .belleville_research import seed_belleville_set_1_research

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "doorhardware.db"
SCHEDULE_UPLOAD_DIR = ROOT / "data" / "schedules"
SCHEDULE_SCHEMA_PATH = ROOT / "SQL" / "sqlite_schedule_schema.sql"

def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def initialize():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, category TEXT NOT NULL, name TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', UNIQUE(category, name))")
        db.execute("CREATE TABLE IF NOT EXISTS rules (id INTEGER PRIMARY KEY, name TEXT NOT NULL, requirements TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS research_notes (id INTEGER PRIMARY KEY, topic TEXT NOT NULL, related_components TEXT NOT NULL, guidance TEXT NOT NULL, source_title TEXT NOT NULL, source_url TEXT NOT NULL, evidence_status TEXT NOT NULL DEFAULT 'research_lead', UNIQUE(topic, source_url))")
        db.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, category TEXT NOT NULL, manufacturer TEXT NOT NULL DEFAULT '', model TEXT NOT NULL, name TEXT NOT NULL, specifications TEXT NOT NULL DEFAULT '{}', source_title TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', evidence_status TEXT NOT NULL DEFAULT 'research_lead', notes TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(category,manufacturer,model))")
        db.execute("CREATE TABLE IF NOT EXISTS compatibility_assertions (id INTEGER PRIMARY KEY, product_ids TEXT NOT NULL, outcome TEXT NOT NULL CHECK(outcome IN ('compatible','incompatible','conditional')), conditions TEXT NOT NULL DEFAULT '{}', rationale TEXT NOT NULL DEFAULT '', source_title TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', evidence_status TEXT NOT NULL DEFAULT 'research_lead', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(product_ids,conditions))")
        db.execute("CREATE TABLE IF NOT EXISTS compatibility_rules (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category_a TEXT NOT NULL, category_b TEXT NOT NULL, spec_a TEXT NOT NULL, comparison TEXT NOT NULL, spec_b TEXT NOT NULL, pass_outcome TEXT NOT NULL DEFAULT 'compatible', fail_outcome TEXT NOT NULL DEFAULT 'incompatible', rationale TEXT NOT NULL DEFAULT '', source_title TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', evidence_status TEXT NOT NULL DEFAULT 'research_lead', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS catalog_scrape_runs (id INTEGER PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, source_results TEXT NOT NULL, products_added INTEGER NOT NULL DEFAULT 0, products_refreshed INTEGER NOT NULL DEFAULT 0, products_unchanged INTEGER NOT NULL DEFAULT 0)")
        db.executescript(SCHEDULE_SCHEMA_PATH.read_text(encoding="utf-8"))
        door_columns = {row["name"] for row in db.execute("PRAGMA table_info(scheduled_doors)")}
        if "door_number_status" not in door_columns:
            db.execute("ALTER TABLE scheduled_doors ADD COLUMN door_number_status TEXT NOT NULL DEFAULT 'known' CHECK (door_number_status IN ('known', 'unknown'))")
        db.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category,active)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_assertions_status ON compatibility_assertions(evidence_status)")
        db.executemany(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES ('automatic_operator',?,?,?,?,?,?, 'research_lead',?)",
            [(brand, model, name, json.dumps(specs), OPERATOR_GUIDE_TITLE, OPERATOR_GUIDE_URL, "Candidate identified in a buying guide; confirm exact model and specifications against manufacturer documentation.") for brand, model, name, specs in OPERATOR_PRODUCTS],
        )
        seed_manufacturer_product_data(db)
        seed_belleville_set_1_research(db)
        for category, names in SEED_ITEMS.items():
            db.executemany(
                "INSERT OR IGNORE INTO items(category,name,notes) VALUES (?,?,?)",
                [(category, name, seed_item_note(category, name)) for name in names],
            )
        if db.execute("SELECT count(*) FROM rules").fetchone()[0] == 0:
            db.executemany("INSERT INTO rules(name,requirements,notes) VALUES (?,?,?)", [(name, json.dumps(req), note) for name, req, note in SEED_RULES])
        db.executemany(
            "INSERT OR IGNORE INTO research_notes(topic,related_components,guidance,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,?)",
            [(topic, components, guidance, OPERATOR_GUIDE_TITLE, OPERATOR_GUIDE_URL, status) for topic, components, guidance, status in SEED_RESEARCH_NOTES],
        )
def item_dict(row):
    return {"id": row["id"], "category": row["category"], "name": row["name"], "notes": row["notes"]}

def seed_item_note(category, name):
    if category == "automatic_operator":
        return f"Model family named in the ZenSupply buying guide; research lead only, verify exact model against manufacturer documentation. Source: {OPERATOR_GUIDE_URL}"
    if category in {"activation_device", "lock_interface", "power_architecture", "safety_device"}:
        return f"Device type or arrangement described in the ZenSupply buying guide; not a compatibility approval. Verify exact product details. Source: {OPERATOR_GUIDE_URL}"
    return ""

def rule_dict(row):
    return {"id": row["id"], "name": row["name"], "requirements": json.loads(row["requirements"]), "notes": row["notes"], "updated_at": row["updated_at"]}

def product_dict(row):
    return {
        "id": row["id"], "category": row["category"], "category_label": PRODUCT_CATEGORIES.get(row["category"], row["category"]),
        "manufacturer": row["manufacturer"], "model": row["model"], "name": row["name"],
        "specifications": json.loads(row["specifications"]), "source_title": row["source_title"],
        "source_url": row["source_url"], "evidence_status": row["evidence_status"],
        "notes": row["notes"], "active": bool(row["active"]), "updated_at": row["updated_at"],
    }

def assertion_dict(row):
    return {
        "id": row["id"], "product_ids": json.loads(row["product_ids"]), "outcome": row["outcome"],
        "conditions": json.loads(row["conditions"]), "rationale": row["rationale"],
        "source_title": row["source_title"], "source_url": row["source_url"],
        "evidence_status": row["evidence_status"], "updated_at": row["updated_at"],
    }

def compatibility_rule_dict(row):
    return {key: row[key] for key in row.keys()}
def trusted_evidence(status):
    return status in {"manufacturer_document", "field_verified", "company_approved"}

def trusted_product_record(product):
    return trusted_evidence(product["evidence_status"]) and product["specifications"].get("record_scope") not in {"series_reference", "model_family"}

def normalized_ids(raw_ids):
    try:
        ids = sorted({int(value) for value in raw_ids if value is not None and value != "" and str(value).casefold() != "null"})
    except (TypeError, ValueError):
        return []
    return ids

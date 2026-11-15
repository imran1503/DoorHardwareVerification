"""Small, dependency-free API and SQLite store for Door Hardware Verification."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sqlite3
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DB_PATH = ROOT / "doorhardware.db"

CATEGORIES = {
    "door_material": "Door material",
    "frame_material": "Frame material",
    "strike": "Strike / lock",
    "operator": "Operator / ADO",
    "automatic_operator": "Automatic operator model",
    "activation_device": "Operator activation device",
    "lock_interface": "Operator lock interface",
    "power_architecture": "Power arrangement",
    "safety_device": "Operator safety device",
    "existing_hardware": "Existing hardware",
    "proposed_hardware": "Proposed hardware",
    "voltage": "Voltage",
    "controller": "Controller / integration",
    "door_location": "Door location",
}

FIELDS = {
    "door_material": "Door material", "frame_material": "Frame material",
    "strike": "Strike / lock", "operator": "Operator handing / ADO type",
    "automatic_operator": "Automatic operator model",
    "activation_device": "Activation device",
    "lock_interface": "Lock interface",
    "power_architecture": "Power arrangement",
    "safety_device": "Safety device",
    "existing_hardware": "Existing hardware", "voltage": "Voltage",
    "controller": "Controller / integration", "swing": "Door swing",
    "proposed_hardware": "Proposed hardware", "door_type": "Door configuration",
    "door_location": "Door location", "fire_rated": "Fire rating",
    "door_contact": "Door contact", "request_to_exit": "Request to exit",
}

MODEL_SPECIFIC_FIELDS = {
    "automatic_operator", "activation_device", "lock_interface",
    "power_architecture", "safety_device",
}

PRODUCT_CATEGORIES = {
    "door": "Door leaf",
    "frame": "Frame",
    "hinge": "Hinge",
    "closer": "Door closer",
    "mechanical_lock": "Mechanical lock / lever / trim",
    "automatic_operator": "Automatic door operator",
    "electric_lock": "Electrified lock",
    "electric_strike": "Electric strike",
    "exit_device": "Exit device",
    "power_supply": "Power supply",
    "controller": "Controller / relay",
    "activation_device": "Activation device",
    "access_control": "Access control reader / panel",
    "request_to_exit": "Request-to-exit device",
    "emergency_release": "Emergency release / push-to-unlock",
    "alarm": "Alarm / annunciator",
    "safety_sensor": "Safety sensor / mat",
    "washroom_control": "Washroom control kit",
    "door_seal": "Door seal / weatherstripping",
    "threshold": "Threshold / saddle",
    "flush_bolt": "Flush bolt",
    "coordinator": "Door coordinator",
    "door_stop": "Door stop / holder",
    "other": "Other component",
}

# Only these component-class pairs are expected to interact in the first coverage view.
# The full product cross-product is never generated.
INTERACTION_PAIRS = [
    ("door", "frame"),
    ("door", "hinge"),
    ("frame", "hinge"),
    ("door", "closer"),
    ("frame", "closer"),
    ("door", "electric_lock"),
    ("door", "electric_strike"),
    ("door", "exit_device"),
    ("door", "mechanical_lock"),
    ("door", "door_seal"),
    ("door", "flush_bolt"),
    ("door", "door_stop"),
    ("frame", "electric_lock"),
    ("frame", "electric_strike"),
    ("frame", "exit_device"),
    ("frame", "mechanical_lock"),
    ("frame", "door_seal"),
    ("frame", "threshold"),
    ("frame", "flush_bolt"),
    ("frame", "coordinator"),
    ("frame", "door_stop"),
    ("frame", "door"),
    ("door", "threshold"),
    ("door", "coordinator"),
    ("door", "closer"),
    ("door", "hinge"),
    ("door", "automatic_operator"),
    ("frame", "automatic_operator"),
    ("hinge", "automatic_operator"),
    ("mechanical_lock", "electric_lock"),
    ("mechanical_lock", "exit_device"),
    ("closer", "automatic_operator"),
    ("automatic_operator", "activation_device"),
    ("automatic_operator", "controller"),
    ("automatic_operator", "access_control"),
    ("automatic_operator", "electric_lock"),
    ("automatic_operator", "electric_strike"),
    ("automatic_operator", "exit_device"),
    ("automatic_operator", "power_supply"),
    ("automatic_operator", "safety_sensor"),
    ("automatic_operator", "door"),
    ("automatic_operator", "frame"),
    ("automatic_operator", "hinge"),
    ("controller", "activation_device"),
    ("controller", "access_control"),
    ("controller", "electric_lock"),
    ("controller", "electric_strike"),
    ("controller", "exit_device"),
    ("controller", "power_supply"),
    ("controller", "request_to_exit"),
    ("controller", "emergency_release"),
    ("controller", "alarm"),
    ("controller", "washroom_control"),
    ("washroom_control", "activation_device"),
    ("washroom_control", "emergency_release"),
    ("washroom_control", "alarm"),
    ("washroom_control", "power_supply"),
    ("washroom_control", "controller"),
    ("washroom_control", "request_to_exit"),
    ("washroom_control", "access_control"),
    ("washroom_control", "electric_lock"),
    ("washroom_control", "electric_strike"),
    ("washroom_control", "exit_device"),
    ("access_control", "electric_lock"),
    ("access_control", "electric_strike"),
    ("access_control", "exit_device"),
    ("request_to_exit", "electric_lock"),
    ("request_to_exit", "electric_strike"),
    ("request_to_exit", "exit_device"),
    ("request_to_exit", "alarm"),
    ("emergency_release", "electric_lock"),
    ("emergency_release", "electric_strike"),
    ("emergency_release", "exit_device"),
    ("emergency_release", "access_control"),
    ("alarm", "controller"),
    ("alarm", "power_supply"),
    ("activation_device", "power_supply"),
    ("safety_sensor", "power_supply"),
    ("emergency_release", "washroom_control"),
    ("electric_lock", "power_supply"),
    ("electric_lock", "controller"),
    ("electric_strike", "power_supply"),
    ("electric_strike", "controller"),
    ("exit_device", "power_supply"),
    ("exit_device", "controller"),
    ("emergency_release", "alarm"),
    ("emergency_release", "power_supply"),
    ("emergency_release", "controller"),
    ("safety_sensor", "automatic_operator"),
]

OPERATOR_PRODUCTS = [
    ("LCN", "9540", "LCN 9540 Senior Swing", {"operator_class": "low_energy", "standard_claim": "ANSI/BHMA A156.19"}),
    ("Norton Rixson", "6000 Series", "Norton Rixson 6000 Series", {"operator_class": "low_energy", "standard_claim": "ANSI/BHMA A156.19"}),
    ("Norton Rixson", "5800 ADAEZ Pro", "Norton Rixson 5800 ADAEZ Pro", {"operator_class": "low_energy", "standard_claim": "ANSI/BHMA A156.19"}),
    ("dormakaba", "ED100", "dormakaba ED100", {"operator_class": "low_energy", "standard_claim": "ANSI/BHMA A156.19"}),
    ("dormakaba", "ED250", "dormakaba ED250", {"operator_class": "low_energy", "standard_claim": "ANSI/BHMA A156.19"}),
    ("Record", "8100", "Record 8100", {"operator_class": "full_power", "standard_claim": "ANSI/BHMA A156.10"}),
]
EVIDENCE_STATUSES = {
    "research_lead": "Research lead",
    "manufacturer_document": "Manufacturer documentation",
    "field_verified": "Field verified",
    "company_approved": "Company approved",
}

SEED_ITEMS = {
    "door_material": ["Wood", "MDF", "Glass", "Metal"],
    "frame_material": ["Steel", "Wood", "Aluminum", "None"],
    "strike": ["Standard Strike 12V", "Mortise Strike 24V", "Magnetic Lock"],
    "operator": ["LH", "LH Reverse", "RH", "RH Reverse", "Maglock", "Electrical Crashbar", "Not Opening", "None"],
    "automatic_operator": ["LCN 9540 Senior Swing", "Norton Rixson 6000 Series", "Norton Rixson 5800 ADAEZ Pro", "dormakaba ED100", "dormakaba ED250", "Record 8100"],
    "activation_device": ["Push plate (hardwired)", "Push plate (wireless/RF)", "Touchless wave sensor", "Card reader", "Building automation signal"],
    "lock_interface": ["Electric strike", "Electric latch retraction exit device"],
    "power_architecture": ["Operator line-voltage feed", "Separate low-voltage access-control supply"],
    "safety_device": ["Presence sensor", "Safety mat", "Guide rail"],
    "existing_hardware": ["None", "Standard Strike", "Mortise Lock", "Electric Lockset", "Maglock", "Electric Crashbar", "Panic Bar"],
    "proposed_hardware": ["None", "Standard Strike", "Mortise Lock", "Electric Lockset", "Maglock", "Electric Crashbar", "Panic Bar"],
    "voltage": ["12V DC", "24V AC", "24V DC"],
    "controller": ["CX-33", "CX-EL331", "Securitron TS-12", "None"],
    "door_location": ["Front", "Rear", "Side", "Office", "Interior", "Exterior", "Other"],
}

SEED_RULES = [
    ("Wood / steel · LH · CX-33", {"door_material":"Wood", "frame_material":"Steel", "strike":"Standard Strike 12V", "operator":"LH", "existing_hardware":"None", "proposed_hardware":"Electric Lockset", "voltage":"12V DC", "controller":"None", "swing":"Left", "door_type":"Single", "door_location":"Front", "fire_rated":"Yes", "door_contact":"Yes", "request_to_exit":"Yes"}, "Installed in lobby"),
    ("Wood / steel · LH reverse · CX-33", {"door_material":"Wood", "frame_material":"Steel", "strike":"Mortise Strike 24V", "operator":"LH Reverse", "existing_hardware":"Mortise Lock", "proposed_hardware":"Electric Lockset", "voltage":"24V AC", "controller":"CX-33", "swing":"Right", "door_type":"Double", "door_location":"Rear", "fire_rated":"No", "door_contact":"No", "request_to_exit":"Yes"}, "Example record from the original project database."),
    ("Glass / aluminum · maglock", {"door_material":"Glass", "frame_material":"Aluminum", "strike":"Magnetic Lock", "operator":"Maglock", "existing_hardware":"Maglock", "proposed_hardware":"Maglock", "voltage":"12V DC", "controller":"Securitron TS-12", "swing":"None", "door_type":"Single", "door_location":"Office", "fire_rated":"No", "door_contact":"Yes", "request_to_exit":"No"}, "Glass door with maglock."),
    ("MDF / wood · RH · crashbar", {"door_material":"MDF", "frame_material":"Wood", "strike":"Standard Strike 12V", "operator":"RH", "existing_hardware":"Standard Strike", "proposed_hardware":"Electric Crashbar", "voltage":"24V AC", "controller":"CX-EL331", "swing":"Left Reverse", "door_type":"Single", "door_location":"Side", "fire_rated":"Yes", "door_contact":"Yes", "request_to_exit":"Yes"}, "Fire rated door with crashbar."),
]

OPERATOR_GUIDE_URL = "https://zensupply.com/blog/commercial-automatic-door-operators-buying-guide"
OPERATOR_GUIDE_TITLE = "Commercial Automatic Door Operators Buying Guide: Specs, Brands & ADA — ZenSupply"
SEED_RESEARCH_NOTES = [
    ("Operator families to investigate", "Automatic operators", "The guide names LCN Senior Swing / 9540, Norton Rixson 6000 and 5800 ADAEZ Pro, dormakaba ED100 and ED250, and Record 8100. Treat these as research candidates; confirm exact current models and whether they are in the company product scope.", "research_lead"),
    ("Operator class", "Automatic operators · activation · safety", "The guide distinguishes low-energy and full-power operators and references ANSI/BHMA A156.19 and A156.10. Capture the manufacturer's declared operator class and required safety setup for each exact model.", "research_lead"),
    ("Door fit and mounting", "Automatic operators · door · frame · hinges", "Collect door width, weight, swing, operator capacity, mounting pattern, frame reinforcement, and hinge requirements. Check each value against the exact operator and opening documentation.", "research_lead"),
    ("Activation inputs", "Automatic operators · push buttons · touchless sensors · readers", "The guide describes push plates, touchless sensors, card readers, and building-automation signals as possible activation sources. Record the operator input type and electrical/interface requirements before pairing devices.", "research_lead"),
    ("Unlock/open sequence", "Automatic operators · access control · strike · electric latch retraction", "The guide describes granting access, releasing the lock, then activating the operator, with delay or latch-retraction sequencing. Record the required sequence and timing from exact manufacturer wiring diagrams; do not apply the article's example delay as a universal value.", "research_lead"),
    ("Locking hardware interface", "Automatic operators · electric strikes · exit devices", "The guide distinguishes electric strikes from electric latch-retraction exit devices. Record the actual lock/exit-device type, frame/door preparation, voltage, and operator/control interface for each product.", "research_lead"),
    ("Power planning", "Automatic operators · power supplies · access-control devices", "The guide calls out operator power and low-voltage access-control power as separate design considerations. Record each device's supply voltage, current draw, inrush, and approved source; verify circuit and supply capacity from manufacturer data.", "research_lead"),
    ("Safety and fire-rated openings", "Automatic operators · sensors · fire alarm · door closer", "The guide flags safety devices for some operator classes and closing/latching behavior for rated openings. Verify requirements against the exact operator listing, door assembly, alarm interface, and applicable primary documentation.", "research_lead"),
    ("Washroom and emergency controls", "CX-33 · push buttons · emergency release · push-to-unlock · alarm", "This operator guide does not establish compatibility for CX-33 washroom kits, emergency release stations, push-to-unlock devices, or alarms. These need their own exact model, wiring, power, and sequence documentation.", "documentation_needed"),
]

def connect():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

def initialize():
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, category TEXT NOT NULL, name TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', UNIQUE(category, name))")
        db.execute("CREATE TABLE IF NOT EXISTS rules (id INTEGER PRIMARY KEY, name TEXT NOT NULL, requirements TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE TABLE IF NOT EXISTS research_notes (id INTEGER PRIMARY KEY, topic TEXT NOT NULL, related_components TEXT NOT NULL, guidance TEXT NOT NULL, source_title TEXT NOT NULL, source_url TEXT NOT NULL, evidence_status TEXT NOT NULL DEFAULT 'research_lead', UNIQUE(topic, source_url))")
        db.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, category TEXT NOT NULL, manufacturer TEXT NOT NULL DEFAULT '', model TEXT NOT NULL, name TEXT NOT NULL, specifications TEXT NOT NULL DEFAULT '{}', source_title TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', evidence_status TEXT NOT NULL DEFAULT 'research_lead', notes TEXT NOT NULL DEFAULT '', active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(category,manufacturer,model))")
        db.execute("CREATE TABLE IF NOT EXISTS compatibility_assertions (id INTEGER PRIMARY KEY, product_ids TEXT NOT NULL, outcome TEXT NOT NULL CHECK(outcome IN ('compatible','incompatible','conditional')), conditions TEXT NOT NULL DEFAULT '{}', rationale TEXT NOT NULL DEFAULT '', source_title TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', evidence_status TEXT NOT NULL DEFAULT 'research_lead', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(product_ids,conditions))")
        db.execute("CREATE TABLE IF NOT EXISTS compatibility_rules (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category_a TEXT NOT NULL, category_b TEXT NOT NULL, spec_a TEXT NOT NULL, comparison TEXT NOT NULL, spec_b TEXT NOT NULL, pass_outcome TEXT NOT NULL DEFAULT 'compatible', fail_outcome TEXT NOT NULL DEFAULT 'incompatible', rationale TEXT NOT NULL DEFAULT '', source_title TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', evidence_status TEXT NOT NULL DEFAULT 'research_lead', updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category,active)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_assertions_status ON compatibility_assertions(evidence_status)")
        db.executemany(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES ('automatic_operator',?,?,?,?,?,?, 'research_lead',?)",
            [(brand, model, name, json.dumps(specs), OPERATOR_GUIDE_TITLE, OPERATOR_GUIDE_URL, "Candidate identified in a buying guide; confirm exact model and specifications against manufacturer documentation.") for brand, model, name, specs in OPERATOR_PRODUCTS],
        )
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

def normalized_ids(raw_ids):
    try:
        ids = sorted({int(value) for value in raw_ids})
    except (TypeError, ValueError):
        return []
    return ids

def compare_specs(left, comparison, right):
    if left is None or right is None:
        return None
    if comparison == "equals": return left == right
    if comparison == "not_equals": return left != right
    if comparison == "contains": return right in left if isinstance(left, (list, str)) else False
    if comparison in {"less_or_equal", "greater_or_equal"}:
        try:
            left_number, right_number = float(left), float(right)
        except (TypeError, ValueError):
            return None
        return left_number <= right_number if comparison == "less_or_equal" else left_number >= right_number
    return None

def pair_evaluation(db, product_a, product_b, context=None):
    # A compatibility record cannot be stronger than the product records it
    # relies on. Keep the pair visible, but do not present its result as verified
    # until both exact models have sourced specifications.
    if not trusted_evidence(product_a["evidence_status"]) or not trusted_evidence(product_b["evidence_status"]):
        return {"status": "unverified", "rationale": "Verify both exact product models and their specifications from primary sources before relying on this pair."}
    pair_ids = sorted([product_a["id"], product_b["id"]])
    pair_json = json.dumps(pair_ids, separators=(",", ":"))
    exact_rows = [assertion_dict(row) for row in db.execute(
        "SELECT * FROM compatibility_assertions WHERE product_ids=? ORDER BY updated_at DESC", (pair_json,)
    ) if len(json.loads(row["product_ids"])) == 2]
    for assertion in exact_rows:
        if not trusted_evidence(assertion["evidence_status"]):
            continue
        conditions = assertion["conditions"]
        if conditions and not all((context or {}).get(key) == value for key, value in conditions.items()):
            continue
        return {"status": assertion["outcome"], "rationale": assertion["rationale"], "source_title": assertion["source_title"], "source_url": assertion["source_url"], "evidence_status": assertion["evidence_status"], "assertion_id": assertion["id"]}

    rules = [compatibility_rule_dict(row) for row in db.execute(
        "SELECT * FROM compatibility_rules WHERE (category_a=? AND category_b=?) OR (category_a=? AND category_b=?) ORDER BY id",
        (product_a["category"], product_b["category"], product_b["category"], product_a["category"]),
    )]
    outcomes = []
    for rule in rules:
        reversed_pair = rule["category_a"] == product_b["category"]
        left_product, right_product = (product_b, product_a) if reversed_pair else (product_a, product_b)
        left = left_product["specifications"].get(rule["spec_a"])
        right = right_product["specifications"].get(rule["spec_b"])
        passed = compare_specs(left, rule["comparison"], right)
        if passed is None:
            outcomes.append({"status": "unverified", "rationale": f"Cannot evaluate {rule['name']}: a required specification is missing or not comparable.", "source_title": rule["source_title"], "source_url": rule["source_url"], "evidence_status": rule["evidence_status"]})
        elif not trusted_evidence(rule["evidence_status"]):
            outcomes.append({"status": "unverified", "rationale": f"Rule '{rule['name']}' still needs verified evidence.", "source_title": rule["source_title"], "source_url": rule["source_url"], "evidence_status": rule["evidence_status"]})
        else:
            outcomes.append({"status": rule["pass_outcome"] if passed else rule["fail_outcome"], "rationale": rule["rationale"], "source_title": rule["source_title"], "source_url": rule["source_url"], "evidence_status": rule["evidence_status"], "rule_id": rule["id"]})
    if not outcomes:
        return {"status": "unverified", "rationale": "No sourced compatibility assertion or applicable rule covers this pair."}
    statuses = [outcome["status"] for outcome in outcomes]
    status = "incompatible" if "incompatible" in statuses else "conditional" if "conditional" in statuses else "unverified" if "unverified" in statuses else "compatible"
    return {"status": status, "rationale": " ".join(outcome["rationale"] for outcome in outcomes if outcome.get("rationale")), "sources": outcomes}

def coverage_rows(db):
    products = [product_dict(row) for row in db.execute("SELECT * FROM products WHERE active=1 ORDER BY category,manufacturer,model")]
    by_category = {}
    for product in products:
        by_category.setdefault(product["category"], []).append(product)
    seen = set()
    rows = []
    for category_a, category_b in INTERACTION_PAIRS:
        category_key = tuple(sorted((category_a, category_b)))
        if category_key in seen:
            continue
        seen.add(category_key)
        for product_a in by_category.get(category_a, []):
            for product_b in by_category.get(category_b, []):
                evaluation = pair_evaluation(db, product_a, product_b)
                rows.append({"product_a": product_a, "product_b": product_b, **evaluation})
    return rows

def coverage_summary(rows):
    counts = {key: 0 for key in ("compatible", "incompatible", "conditional", "unverified")}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    counts["total"] = len(rows)
    counts["assessed"] = counts["compatible"] + counts["incompatible"] + counts["conditional"]
    return counts

def opening_fit_findings(products, opening):
    """Compare a supplied opening profile only with explicit sourced model limits."""
    if not opening:
        return []
    relevant_categories = {"automatic_operator", "door", "frame", "hinge", "closer", "mechanical_lock", "electric_lock", "electric_strike", "exit_device"}
    findings = []
    discrete_limits = {
        "door_materials": "door_material",
        "frame_materials": "frame_material",
        "configurations": "configuration",
        "swings": "swing",
        "locations": "location",
    }
    numeric_limits = {
        "max_width_in": ("width_in", "max"),
        "min_width_in": ("width_in", "min"),
        "max_height_in": ("height_in", "max"),
        "min_height_in": ("height_in", "min"),
        "max_weight_lb": ("weight_lb", "max"),
        "min_weight_lb": ("weight_lb", "min"),
    }
    for product in products:
        if product["category"] not in relevant_categories:
            continue
        limits = product["specifications"].get("opening_limits")
        if not trusted_evidence(product["evidence_status"]):
            findings.append({"status": "unverified", "product_a": product, "rationale": f"{product['name']} needs sourced product specifications before it can be checked against this opening."})
            continue
        if not isinstance(limits, dict) or not limits:
            findings.append({"status": "unverified", "product_a": product, "rationale": f"No sourced opening-fit limits are recorded for {product['name']}."})
            continue
        failures, missing = [], []
        for limit_key, context_key in discrete_limits.items():
            if limit_key not in limits:
                continue
            if not isinstance(limits[limit_key], list):
                missing.append(f"valid {limit_key.replace('_', ' ')} product data")
                continue
            value = opening.get(context_key)
            if value in (None, ""):
                missing.append(context_key.replace("_", " "))
            elif value not in limits[limit_key]:
                failures.append(f"{context_key.replace('_', ' ')} {value} is outside the documented range")
        for limit_key, (context_key, direction) in numeric_limits.items():
            if limit_key not in limits:
                continue
            value = opening.get(context_key)
            if value in (None, ""):
                missing.append(context_key.replace("_", " "))
                continue
            try:
                value, bound = float(value), float(limits[limit_key])
            except (TypeError, ValueError):
                missing.append(context_key.replace("_", " "))
                continue
            if (direction == "max" and value > bound) or (direction == "min" and value < bound):
                failures.append(f"{context_key.replace('_', ' ')} {value:g} is outside the documented limit {bound:g}")
        if "supports_fire_rated" in limits:
            rated = opening.get("fire_rated")
            if rated in (None, ""):
                missing.append("fire rating")
            elif rated == "yes" and not limits["supports_fire_rated"]:
                failures.append("the model is not documented for a fire-rated opening")
        if failures:
            status, rationale = "incompatible", "; ".join(failures) + "."
        elif missing:
            status, rationale = "unverified", "Opening information is missing for documented limits: " + ", ".join(sorted(set(missing))) + "."
        else:
            status, rationale = "compatible", "The supplied opening details are within the recorded model limits."
        findings.append({"status": status, "product_a": product, "rationale": rationale, "source_title": product["source_title"], "source_url": product["source_url"]})
    return findings

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")

    def do_OPTIONS(self): self.send_json({})

    def do_GET(self):
        path = urlparse(self.path).path
        with connect() as db:
            if path == "/api/bootstrap":
                items = [item_dict(r) for r in db.execute("SELECT * FROM items ORDER BY category,name")]
                rules = [rule_dict(r) for r in db.execute("SELECT * FROM rules ORDER BY id DESC")]
                research_notes = [dict(r) for r in db.execute("SELECT * FROM research_notes ORDER BY id")]
                products = [product_dict(r) for r in db.execute("SELECT * FROM products WHERE active=1 ORDER BY category,manufacturer,model")]
                assertions = [assertion_dict(r) for r in db.execute("SELECT * FROM compatibility_assertions ORDER BY id DESC")]
                compatibility_rules = [compatibility_rule_dict(r) for r in db.execute("SELECT * FROM compatibility_rules ORDER BY id DESC")]
                return self.send_json({"items": items, "rules": rules, "researchNotes": research_notes, "categories": CATEGORIES, "fields": FIELDS, "products": products, "productCategories": PRODUCT_CATEGORIES, "assertions": assertions, "compatibilityRules": compatibility_rules, "evidenceStatuses": EVIDENCE_STATUSES})
            if path == "/api/coverage":
                rows = coverage_rows(db)
                return self.send_json({"rows": rows, "summary": coverage_summary(rows), "interactionPairs": INTERACTION_PAIRS})
            if path == "/api/health":
                db.execute("SELECT 1").fetchone()
                return self.send_json({"ok": True, "database": "sqlite"})
        self.send_json({"error":"Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.read_json()
        with connect() as db:
            if path == "/api/products":
                return self.create_product(db, data)
            if path == "/api/products/import":
                rows = data.get("products", [])
                if not isinstance(rows, list): return self.send_json({"error": "Expected a products array."}, 400)
                created, updated, errors = 0, 0, []
                for index, product in enumerate(rows, 1):
                    try:
                        result = self.save_product(db, product, import_mode=True)
                        created += result == "created"
                        updated += result == "updated"
                    except (ValueError, sqlite3.IntegrityError) as error:
                        errors.append({"row": index, "error": str(error)})
                return self.send_json({"created": created, "updated": updated, "errors": errors}, 200 if not errors else 207)
            if path == "/api/assertions":
                return self.create_assertion(db, data)
            if path == "/api/compatibility-rules":
                return self.create_compatibility_rule(db, data)
            if path == "/api/items":
                category, name = data.get("category"), str(data.get("name", "")).strip()
                if category not in CATEGORIES or not name: return self.send_json({"error":"Choose a category and enter a name."}, 400)
                try:
                    cur = db.execute("INSERT INTO items(category,name,notes) VALUES (?,?,?)", (category,name,str(data.get("notes", "")).strip()))
                    return self.send_json(item_dict(db.execute("SELECT * FROM items WHERE id=?", (cur.lastrowid,)).fetchone()), 201)
                except sqlite3.IntegrityError: return self.send_json({"error":"That item already exists in this category."}, 409)
            if path == "/api/rules":
                name = str(data.get("name", "")).strip()
                req = data.get("requirements", {})
                if not name or not isinstance(req, dict): return self.send_json({"error":"A rule name and requirements are required."}, 400)
                cur = db.execute("INSERT INTO rules(name,requirements,notes,updated_at) VALUES (?,?,?,CURRENT_TIMESTAMP)", (name,json.dumps(req),str(data.get("notes", "")).strip()))
                return self.send_json(rule_dict(db.execute("SELECT * FROM rules WHERE id=?", (cur.lastrowid,)).fetchone()), 201)
        if path == "/api/check": return self.check(data)
        if path == "/api/compatibility/check": return self.check_assembly(data)
        self.send_json({"error":"Not found"}, 404)

    def save_product(self, db, data, import_mode=False, product_id=None):
        category = str(data.get("category", "")).strip()
        model = str(data.get("model", "")).strip()
        name = str(data.get("name", "")).strip() or model
        manufacturer = str(data.get("manufacturer", "")).strip()
        specifications = data.get("specifications", {})
        if isinstance(specifications, str):
            try: specifications = json.loads(specifications or "{}")
            except json.JSONDecodeError as error: raise ValueError("Specifications must be valid JSON.") from error
        if category not in PRODUCT_CATEGORIES: raise ValueError("Choose a valid product category.")
        if not model or not name: raise ValueError("Product model and name are required.")
        if not isinstance(specifications, dict): raise ValueError("Specifications must be a JSON object.")
        status = data.get("evidence_status", "research_lead")
        if status not in EVIDENCE_STATUSES: raise ValueError("Choose a valid evidence status.")
        values = (category,manufacturer,model,name,json.dumps(specifications),str(data.get("source_title", "")).strip(),str(data.get("source_url", "")).strip(),status,str(data.get("notes", "")).strip())
        if status != "research_lead" and not values[6]: raise ValueError("Add a source URL before marking product data verified.")
        if product_id:
            cur = db.execute("UPDATE products SET category=?,manufacturer=?,model=?,name=?,specifications=?,source_title=?,source_url=?,evidence_status=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (*values,product_id))
            if not cur.rowcount: raise ValueError("Product not found.")
            return "updated"
        existing = db.execute("SELECT id FROM products WHERE category=? AND manufacturer=? AND model=?", (category,manufacturer,model)).fetchone()
        if existing:
            if not import_mode: raise sqlite3.IntegrityError("This category, manufacturer, and model already exist.")
            db.execute("UPDATE products SET name=?,specifications=?,source_title=?,source_url=?,evidence_status=?,notes=?,active=1,updated_at=CURRENT_TIMESTAMP WHERE id=?", (name,json.dumps(specifications),values[5],values[6],status,values[8],existing["id"]))
            return "updated"
        db.execute("INSERT INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)", values)
        return "created"

    def create_product(self, db, data):
        try:
            self.save_product(db, data)
        except (ValueError, sqlite3.IntegrityError) as error:
            return self.send_json({"error": str(error)}, 400)
        product = db.execute("SELECT * FROM products WHERE category=? AND manufacturer=? AND model=?", (data.get("category"),str(data.get("manufacturer", "")).strip(),str(data.get("model", "")).strip())).fetchone()
        return self.send_json(product_dict(product), 201)

    def create_assertion(self, db, data):
        product_ids = normalized_ids(data.get("product_ids", []))
        outcome = data.get("outcome")
        conditions = data.get("conditions", {})
        status = data.get("evidence_status", "research_lead")
        if len(product_ids) < 2: return self.send_json({"error": "Choose at least two distinct products."}, 400)
        if outcome not in {"compatible", "incompatible", "conditional"}: return self.send_json({"error": "Choose a compatibility outcome."}, 400)
        if status not in EVIDENCE_STATUSES: return self.send_json({"error": "Choose a valid evidence status."}, 400)
        if not isinstance(conditions, dict): return self.send_json({"error": "Conditions must be an object."}, 400)
        source_title, source_url = str(data.get("source_title", "")).strip(), str(data.get("source_url", "")).strip()
        if status != "research_lead" and not source_url: return self.send_json({"error": "Add a source URL before marking an assertion verified."}, 400)
        missing = [pid for pid in product_ids if not db.execute("SELECT id FROM products WHERE id=? AND active=1", (pid,)).fetchone()]
        if missing: return self.send_json({"error": "One or more selected products are unavailable."}, 400)
        products_json = json.dumps(product_ids, separators=(",", ":"))
        conditions_json = json.dumps(conditions, sort_keys=True, separators=(",", ":"))
        try:
            cur = db.execute("INSERT INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status,updated_at) VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", (products_json,outcome,conditions_json,str(data.get("rationale", "")).strip(),source_title,source_url,status))
        except sqlite3.IntegrityError:
            return self.send_json({"error": "An assertion for those products and conditions already exists. Edit the existing assertion."}, 409)
        return self.send_json(assertion_dict(db.execute("SELECT * FROM compatibility_assertions WHERE id=?", (cur.lastrowid,)).fetchone()), 201)

    def create_compatibility_rule(self, db, data):
        comparison = data.get("comparison")
        allowed_comparisons = {"equals", "not_equals", "less_or_equal", "greater_or_equal", "contains"}
        status = data.get("evidence_status", "research_lead")
        if not str(data.get("name", "")).strip(): return self.send_json({"error": "Rule name is required."}, 400)
        if data.get("category_a") not in PRODUCT_CATEGORIES or data.get("category_b") not in PRODUCT_CATEGORIES: return self.send_json({"error": "Choose valid component categories."}, 400)
        if comparison not in allowed_comparisons: return self.send_json({"error": "Choose a supported comparison."}, 400)
        if data.get("pass_outcome", "compatible") not in {"compatible", "incompatible", "conditional"} or data.get("fail_outcome", "incompatible") not in {"compatible", "incompatible", "conditional"}: return self.send_json({"error": "Choose valid outcomes."}, 400)
        if status not in EVIDENCE_STATUSES: return self.send_json({"error": "Choose a valid evidence status."}, 400)
        source_url = str(data.get("source_url", "")).strip()
        if status != "research_lead" and not source_url: return self.send_json({"error": "Add a source URL before activating a rule."}, 400)
        cur = db.execute("INSERT INTO compatibility_rules(name,category_a,category_b,spec_a,comparison,spec_b,pass_outcome,fail_outcome,rationale,source_title,source_url,evidence_status,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)", (str(data["name"]).strip(),data["category_a"],data["category_b"],str(data.get("spec_a", "")).strip(),comparison,str(data.get("spec_b", "")).strip(),data.get("pass_outcome", "compatible"),data.get("fail_outcome", "incompatible"),str(data.get("rationale", "")).strip(),str(data.get("source_title", "")).strip(),source_url,status))
        return self.send_json(compatibility_rule_dict(db.execute("SELECT * FROM compatibility_rules WHERE id=?", (cur.lastrowid,)).fetchone()), 201)

    def check(self, data):
        with connect() as db:
            rules = [rule_dict(r) for r in db.execute("SELECT * FROM rules")]
        matches = []
        for rule in rules:
            req = rule["requirements"]
            # Legacy sample rules predate exact operator/product selection.
            # They must not verify a setup after a specific device is selected.
            if any(data.get(key) and req.get(key) != data.get(key) for key in MODEL_SPECIFIC_FIELDS):
                continue
            # Empty requirements represent a wildcard; a verdict needs a fully specified rule.
            constrained = {k:v for k,v in req.items() if v not in (None, "", "Any")}
            if constrained and all(data.get(k) == v for k,v in constrained.items()):
                matches.append((len(constrained), rule))
        if matches:
            matches.sort(key=lambda pair: pair[0], reverse=True)
            best_score = matches[0][0]
            best = [r for score,r in matches if score == best_score]
            if len(best) == 1:
                return self.send_json({"status":"compatible", "rule":best[0]})
            return self.send_json({"status":"review", "rules":best, "message":"More than one equally specific rule applies. Review the records."})
        return self.send_json({"status":"unverified", "message":"No matching compatibility rule is in the library. Add a verified rule before relying on this combination."})

    def check_assembly(self, data):
        product_ids = normalized_ids(data.get("product_ids", []))
        if len(product_ids) < 2:
            return self.send_json({"error": "Choose at least two products to check."}, 400)
        with connect() as db:
            products = [product_dict(row) for row in db.execute(
                f"SELECT * FROM products WHERE active=1 AND id IN ({','.join('?' for _ in product_ids)}) ORDER BY category,manufacturer,model",
                product_ids,
            )]
            if len(products) != len(product_ids):
                return self.send_json({"error": "One or more selected products were not found."}, 404)
            set_key = json.dumps(product_ids, separators=(",", ":"))
            exact = db.execute("SELECT * FROM compatibility_assertions WHERE product_ids=? ORDER BY updated_at DESC LIMIT 1", (set_key,)).fetchone()
            context = data.get("context", {}) if isinstance(data.get("context", {}), dict) else {}
            opening = data.get("opening", {}) if isinstance(data.get("opening", {}), dict) else {}
            context = {**opening, **context}
            if exact:
                assertion = assertion_dict(exact)
                conditions_match = all(context.get(key) == value for key, value in assertion["conditions"].items())
                products_documented = all(trusted_evidence(product["evidence_status"]) for product in products)
                if trusted_evidence(assertion["evidence_status"]) and conditions_match and products_documented:
                    return self.send_json({"status": assertion["outcome"], "assertion": assertion, "products": products, "findings": [{"status": assertion["outcome"], "rationale": assertion["rationale"], "source_title": assertion["source_title"], "source_url": assertion["source_url"]}]})
            findings = []
            for left_index, product_a in enumerate(products):
                for product_b in products[left_index + 1:]:
                    evaluation = pair_evaluation(db, product_a, product_b, context)
                    findings.append({"product_a": product_a, "product_b": product_b, **evaluation})
            findings.extend(opening_fit_findings(products, opening))
            if not all(trusted_evidence(product["evidence_status"]) for product in products):
                findings.append({"status": "unverified", "rationale": "At least one selected product is still a research lead; verify its exact model and specifications from a primary source."})
            if len(products) > 2:
                findings.append({"status": "unverified", "rationale": "Pair checks do not prove the complete multi-device assembly. Add an assembly-level assertion or test record."})
            statuses = [finding["status"] for finding in findings]
            status = "incompatible" if "incompatible" in statuses else "conditional" if "conditional" in statuses else "unverified" if "unverified" in statuses else "compatible"
            messages = {
                "compatible": "All applicable checks passed using sourced product data.",
                "incompatible": "At least one selected product pair has a documented conflict.",
                "conditional": "A documented condition must be satisfied before this combination can be used.",
                "unverified": "Some selected products or interactions do not have enough verified evidence yet.",
            }
            return self.send_json({"status": status, "message": messages[status], "products": products, "findings": findings})

    def do_PUT(self):
        path = urlparse(self.path).path
        data = self.read_json()
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "products":
            with connect() as db:
                try:
                    self.save_product(db, data, product_id=parts[2])
                except (ValueError, sqlite3.IntegrityError) as error:
                    return self.send_json({"error": str(error)}, 400)
                return self.send_json(product_dict(db.execute("SELECT * FROM products WHERE id=?", (parts[2],)).fetchone()))
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "assertions":
            product_ids = normalized_ids(data.get("product_ids", []))
            status, outcome = data.get("evidence_status", "research_lead"), data.get("outcome")
            conditions = data.get("conditions", {})
            if len(product_ids) < 2 or outcome not in {"compatible", "incompatible", "conditional"} or status not in EVIDENCE_STATUSES or not isinstance(conditions, dict):
                return self.send_json({"error": "Assertion needs at least two products, a valid outcome, conditions, and evidence status."}, 400)
            if status != "research_lead" and not str(data.get("source_url", "")).strip():
                return self.send_json({"error": "Add a source URL before marking an assertion verified."}, 400)
            with connect() as db:
                cur = db.execute("UPDATE compatibility_assertions SET product_ids=?,outcome=?,conditions=?,rationale=?,source_title=?,source_url=?,evidence_status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (json.dumps(product_ids,separators=(",", ":")),outcome,json.dumps(conditions,sort_keys=True,separators=(",", ":")),str(data.get("rationale", "")).strip(),str(data.get("source_title", "")).strip(),str(data.get("source_url", "")).strip(),status,parts[2]))
                if not cur.rowcount: return self.send_json({"error": "Assertion not found."}, 404)
                return self.send_json(assertion_dict(db.execute("SELECT * FROM compatibility_assertions WHERE id=?", (parts[2],)).fetchone()))
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "compatibility-rules":
            with connect() as db:
                cur = db.execute("UPDATE compatibility_rules SET name=?,category_a=?,category_b=?,spec_a=?,comparison=?,spec_b=?,pass_outcome=?,fail_outcome=?,rationale=?,source_title=?,source_url=?,evidence_status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (str(data.get("name", "")).strip(),data.get("category_a"),data.get("category_b"),str(data.get("spec_a", "")).strip(),data.get("comparison"),str(data.get("spec_b", "")).strip(),data.get("pass_outcome", "compatible"),data.get("fail_outcome", "incompatible"),str(data.get("rationale", "")).strip(),str(data.get("source_title", "")).strip(),str(data.get("source_url", "")).strip(),data.get("evidence_status", "research_lead"),parts[2]))
                if not cur.rowcount: return self.send_json({"error": "Compatibility rule not found."}, 404)
                return self.send_json(compatibility_rule_dict(db.execute("SELECT * FROM compatibility_rules WHERE id=?", (parts[2],)).fetchone()))
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "items":
            category, name = data.get("category"), str(data.get("name", "")).strip()
            if category not in CATEGORIES or not name: return self.send_json({"error":"Choose a category and enter a name."}, 400)
            with connect() as db:
                try:
                    cur = db.execute("UPDATE items SET category=?,name=?,notes=? WHERE id=?", (category,name,str(data.get("notes", "")).strip(),parts[2]))
                    if not cur.rowcount: return self.send_json({"error":"Item not found"},404)
                    return self.send_json(item_dict(db.execute("SELECT * FROM items WHERE id=?",(parts[2],)).fetchone()))
                except sqlite3.IntegrityError: return self.send_json({"error":"That item already exists in this category."}, 409)
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "rules":
            with connect() as db:
                cur = db.execute("UPDATE rules SET name=?,requirements=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (str(data.get("name", "")).strip(),json.dumps(data.get("requirements",{})),str(data.get("notes", "")).strip(),parts[2]))
                if not cur.rowcount: return self.send_json({"error":"Rule not found"},404)
                return self.send_json(rule_dict(db.execute("SELECT * FROM rules WHERE id=?",(parts[2],)).fetchone()))
        self.send_json({"error":"Not found"}, 404)

    def do_DELETE(self):
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "api":
            if parts[1] == "products":
                with connect() as db:
                    cur = db.execute("UPDATE products SET active=0,updated_at=CURRENT_TIMESTAMP WHERE id=?", (parts[2],))
                    if cur.rowcount: return self.send_json({"deleted": True, "soft_delete": True})
            table = {"items":"items", "rules":"rules", "assertions":"compatibility_assertions", "compatibility-rules":"compatibility_rules"}.get(parts[1])
            if table:
                with connect() as db:
                    cur = db.execute(f"DELETE FROM {table} WHERE id=?", (parts[2],))
                    if cur.rowcount: return self.send_json({"deleted":True})
        self.send_json({"error":"Not found"}, 404)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

if __name__ == "__main__":
    initialize()
    print(f"Door hardware API ready at http://127.0.0.1:8000 · SQLite: {DB_PATH}")
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()

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
    "existing_hardware": "Existing hardware",
    "proposed_hardware": "Proposed hardware",
    "voltage": "Voltage",
    "controller": "Controller / integration",
    "door_location": "Door location",
}

FIELDS = {
    "door_material": "Door material", "frame_material": "Frame material",
    "strike": "Strike / lock", "operator": "Operator / ADO",
    "existing_hardware": "Existing hardware", "voltage": "Voltage",
    "controller": "Controller / integration", "swing": "Door swing",
    "proposed_hardware": "Proposed hardware", "door_type": "Door configuration",
    "door_location": "Door location", "fire_rated": "Fire rating",
    "door_contact": "Door contact", "request_to_exit": "Request to exit",
}

SEED_ITEMS = {
    "door_material": ["Wood", "MDF", "Glass", "Metal"],
    "frame_material": ["Steel", "Wood", "Aluminum", "None"],
    "strike": ["Standard Strike 12V", "Mortise Strike 24V", "Magnetic Lock"],
    "operator": ["LH", "LH Reverse", "RH", "RH Reverse", "Maglock", "Electrical Crashbar", "Not Opening", "None"],
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
        count = db.execute("SELECT count(*) FROM items").fetchone()[0]
        if count == 0:
            for category, names in SEED_ITEMS.items():
                db.executemany("INSERT INTO items(category,name) VALUES (?,?)", [(category, name) for name in names])
        if db.execute("SELECT count(*) FROM rules").fetchone()[0] == 0:
            db.executemany("INSERT INTO rules(name,requirements,notes) VALUES (?,?,?)", [(name, json.dumps(req), note) for name, req, note in SEED_RULES])
        db.executemany(
            "INSERT OR IGNORE INTO research_notes(topic,related_components,guidance,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,?)",
            [(topic, components, guidance, OPERATOR_GUIDE_TITLE, OPERATOR_GUIDE_URL, status) for topic, components, guidance, status in SEED_RESEARCH_NOTES],
        )

def item_dict(row):
    return {"id": row["id"], "category": row["category"], "name": row["name"], "notes": row["notes"]}

def rule_dict(row):
    return {"id": row["id"], "name": row["name"], "requirements": json.loads(row["requirements"]), "notes": row["notes"], "updated_at": row["updated_at"]}

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
                return self.send_json({"items": items, "rules": rules, "researchNotes": research_notes, "categories": CATEGORIES, "fields": FIELDS})
            if path == "/api/health":
                db.execute("SELECT 1").fetchone()
                return self.send_json({"ok": True, "database": "sqlite"})
        self.send_json({"error":"Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.read_json()
        with connect() as db:
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
        self.send_json({"error":"Not found"}, 404)

    def check(self, data):
        with connect() as db:
            rules = [rule_dict(r) for r in db.execute("SELECT * FROM rules")]
        matches = []
        for rule in rules:
            req = rule["requirements"]
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

    def do_PUT(self):
        path = urlparse(self.path).path
        data = self.read_json()
        parts = path.strip("/").split("/")
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
            table = {"items":"items", "rules":"rules"}.get(parts[1])
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

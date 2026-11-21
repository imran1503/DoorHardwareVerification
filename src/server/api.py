"""HTTP API routes for the Door Hardware Verification app."""
from http.server import BaseHTTPRequestHandler
import base64
import binascii
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import parse_qs, urlparse

from .catalog import CATEGORIES, EVIDENCE_STATUSES, FIELDS, INTERACTION_PAIRS, MODEL_SPECIFIC_FIELDS, PRODUCT_CATEGORIES
from .compatibility import assembly_estimate, assembly_subset_checks, coverage_rows, coverage_summary, pair_estimate, pair_evaluation, pair_is_applicable, power_path_findings
from .database import (
    assertion_dict, compatibility_rule_dict, connect, item_dict, normalized_ids,
    product_dict, rule_dict, SCHEDULE_UPLOAD_DIR, trusted_evidence, trusted_product_record,
)
from .opening_fit import opening_fit_findings
from .catalog_refresh import refresh_catalogs
from .schedule_import import extract_schedule


class _JsonHarness:
    """Small response capture used to reuse the assembly evaluator for saved runs."""
    def send_json(self, data, status=200):
        self.response = (status, data)
        return self.response


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

    def send_bytes(self, body, content_type, filename=None):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if filename:
            self.send_header("Content-Disposition", f'inline; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")

    def do_OPTIONS(self): self.send_json({})

    def do_GET(self):
        path = urlparse(self.path).path
        with connect() as db:
            if path == "/api/projects":
                return self.list_projects(db)
            if path.startswith("/api/projects/"):
                parts = path.strip("/").split("/")
                if len(parts) == 3 and parts[2].isdigit():
                    return self.get_project(db, int(parts[2]))
                if len(parts) == 4 and parts[2] == "runs" and parts[3].isdigit():
                    return self.get_verification_run(db, int(parts[3]))
            if path.startswith("/api/schedule-revisions/") and path.endswith("/pages"):
                parts = path.strip("/").split("/")
                if len(parts) == 4 and parts[2].isdigit():
                    return self.get_schedule_pages(db, int(parts[2]))
            if path.startswith("/api/schedule-sources/") and path.endswith("/file"):
                parts = path.strip("/").split("/")
                if len(parts) == 4 and parts[2].isdigit():
                    return self.get_schedule_file(db, int(parts[2]))
            if path.startswith("/api/verification-runs/") and path.split("/")[-1].isdigit():
                return self.get_verification_run(db, int(path.split("/")[-1]))
            if path == "/api/catalog/status":
                row = db.execute("SELECT * FROM catalog_scrape_runs ORDER BY id DESC LIMIT 1").fetchone()
                if not row:
                    return self.send_json({"last_run": None})
                latest = dict(row)
                latest["source_results"] = json.loads(latest["source_results"])
                return self.send_json({"last_run": latest})
            if path == "/api/bootstrap":
                items = [item_dict(r) for r in db.execute("SELECT * FROM items ORDER BY category,name")]
                rules = [rule_dict(r) for r in db.execute("SELECT * FROM rules ORDER BY id DESC")]
                research_notes = [dict(r) for r in db.execute("SELECT * FROM research_notes ORDER BY id")]
                products = [product_dict(r) for r in db.execute("SELECT * FROM products WHERE active=1 ORDER BY category,manufacturer,model")]
                assertions = [assertion_dict(r) for r in db.execute("SELECT * FROM compatibility_assertions ORDER BY id DESC")]
                compatibility_rules = [compatibility_rule_dict(r) for r in db.execute("SELECT * FROM compatibility_rules ORDER BY id DESC")]
                return self.send_json({"items": items, "rules": rules, "researchNotes": research_notes, "categories": CATEGORIES, "fields": FIELDS, "products": products, "productCategories": PRODUCT_CATEGORIES, "assertions": assertions, "compatibilityRules": compatibility_rules, "evidenceStatuses": EVIDENCE_STATUSES})
            if path == "/api/coverage":
                query = parse_qs(urlparse(self.path).query)
                rows = coverage_rows(db)
                summary = coverage_summary(rows)
                status_filter = query.get("status", ["applicable"])[0]
                search = query.get("q", [""])[0].strip().casefold()
                if status_filter == "applicable":
                    filtered = [row for row in rows if row.get("applicable")]
                elif status_filter == "all":
                    filtered = rows
                else:
                    filtered = [row for row in rows if row.get("status") == status_filter]
                if search:
                    filtered = [row for row in filtered if search in " ".join((row["product_a"].get("name", ""), row["product_a"].get("manufacturer", ""), row["product_a"].get("model", ""), row["product_b"].get("name", ""), row["product_b"].get("manufacturer", ""), row["product_b"].get("model", ""), *(product.get("model", "") for evidence in row.get("assembly_evidence", []) for product in evidence.get("products", [])))).casefold()]
                try:
                    page = max(1, int(query.get("page", ["1"])[0]))
                    page_size = min(100, max(1, int(query.get("page_size", ["50"])[0])))
                except ValueError:
                    page, page_size = 1, 50
                total_filtered = len(filtered)
                start = (page - 1) * page_size
                return self.send_json({"rows": filtered[start:start + page_size], "summary": summary, "interactionPairs": INTERACTION_PAIRS, "page": page, "page_size": page_size, "total_filtered": total_filtered, "pages": (total_filtered + page_size - 1) // page_size, "filter": status_filter, "query": search})
            if path == "/api/health":
                db.execute("SELECT 1").fetchone()
                return self.send_json({"ok": True, "database": "sqlite"})
        self.send_json({"error":"Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        data = self.read_json()
        if path == "/api/catalog/refresh":
            try:
                return self.send_json(refresh_catalogs())
            except RuntimeError as error:
                return self.send_json({"error": str(error)}, 409)
            except Exception as error:
                return self.send_json({"error": f"Catalog refresh failed: {error}"}, 502)
        with connect() as db:
            if path == "/api/projects/import-schedule":
                return self.import_schedule(db, data)
            if path == "/api/projects/doors":
                return self.add_project_door(db, data)
            if path == "/api/projects/sets":
                return self.add_project_set(db, data)
            if path == "/api/scheduled-items/matches":
                return self.save_schedule_match(db, data)
            if path.startswith("/api/projects/") and path.endswith("/verify"):
                parts = path.strip("/").split("/")
                if len(parts) == 4 and parts[2].isdigit():
                    return self.verify_project(db, int(parts[2]), data)
            if path.startswith("/api/hardware-sets/") and path.endswith("/items"):
                parts = path.strip("/").split("/")
                if len(parts) == 4 and parts[2].isdigit():
                    return self.add_schedule_item(db, int(parts[2]), data)
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
            if path == "/api/evidence/import":
                return self.import_evidence_bundle(db, data)
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
        if path == "/api/opening-fit":
            product_ids = normalized_ids(data.get("product_ids", []))
            opening = data.get("opening", {}) if isinstance(data.get("opening", {}), dict) else {}
            with connect() as db:
                products = [product_dict(row) for row in db.execute(
                    f"SELECT * FROM products WHERE active=1 AND id IN ({','.join('?' for _ in product_ids)}) ORDER BY category,manufacturer,model",
                    product_ids,
                )] if product_ids else []
                findings = opening_fit_findings(products, opening)
                if not products:
                    return self.send_json({"status": "unverified", "message": "Opening details are entered, but no product is selected to compare them against.", "findings": [], "products": []})
                for field, category, label in [("door_material", "door", "door material"), ("frame_material", "frame", "frame material")]:
                    if opening.get(field) not in (None, "") and not any(product["category"] == category for product in products):
                        findings.append({"status": "unverified", "rationale": f"{label.title()} is recorded, but no {label} model is selected to compare it against."})
                if not findings:
                    return self.send_json({"status": "unverified", "message": "These selected product categories do not have opening-fit limits to compare. Add a door, frame, operator or other model with documented opening constraints.", "findings": [], "products": products})
                statuses = [finding["status"] for finding in findings]
                status = "incompatible" if "incompatible" in statuses else "conditional" if "conditional" in statuses else "unverified" if "unverified" in statuses else "compatible"
                messages = {
                    "compatible": "Opening details fit within the selected products' recorded limits.",
                    "incompatible": "An opening detail conflicts with a selected product.",
                    "conditional": "A documented condition must be satisfied for this opening.",
                    "unverified": "The opening details are being checked, but exact product data or configuration is still needed.",
                }
                return self.send_json({"status": status, "message": messages[status], "findings": findings, "products": products})
        if path == "/api/compatibility/check": return self.check_assembly(data)
        self.send_json({"error":"Not found"}, 404)

    def list_projects(self, db):
        rows = db.execute(
            "SELECT p.*, (SELECT COUNT(*) FROM schedule_revisions r WHERE r.project_id=p.id) AS revision_count, "
            "(SELECT COUNT(*) FROM scheduled_doors d JOIN schedule_revisions r ON r.id=d.schedule_revision_id WHERE r.project_id=p.id) AS door_count "
            "FROM projects p ORDER BY p.updated_at DESC,p.id DESC"
        ).fetchall()
        return self.send_json({"projects": [dict(row) for row in rows]})

    def get_project(self, db, project_id):
        project = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if not project:
            return self.send_json({"error": "Project not found."}, 404)
        revisions = [dict(row) for row in db.execute(
            "SELECT r.*,s.title AS source_title,s.local_path,s.document_sha256 "
            "FROM schedule_revisions r JOIN evidence_sources s ON s.id=r.evidence_source_id "
            "WHERE r.project_id=? ORDER BY r.imported_at DESC,r.id DESC", (project_id,)
        )]
        revision_ids = [row["id"] for row in revisions]
        revision_id = revision_ids[0] if revision_ids else None
        doors, sets, issues, runs = [], [], [], []
        if revision_id:
            for row in db.execute("SELECT * FROM scheduled_doors WHERE schedule_revision_id=? ORDER BY door_number,source_row_number", (revision_id,)):
                door = dict(row)
                door["assignments"] = []
                for assignment in db.execute(
                    "SELECT a.*,h.set_code,h.description AS set_description,h.source_notes,h.source_start_page,h.source_end_page "
                    "FROM door_set_assignments a JOIN hardware_sets h ON h.id=a.hardware_set_id WHERE a.scheduled_door_id=? ORDER BY h.set_code", (door["id"],)
                ):
                    set_value = dict(assignment)
                    set_value["items"] = Handler._set_items(db, assignment["hardware_set_id"])
                    door["assignments"].append(set_value)
                doors.append(door)
            for row in db.execute("SELECT * FROM hardware_sets WHERE schedule_revision_id=? ORDER BY set_code,occurrence_number", (revision_id,)):
                set_value = dict(row)
                set_value["items"] = Handler._set_items(db, row["id"])
                sets.append(set_value)
            issues = [dict(row) for row in db.execute(
                "SELECT * FROM import_review_issues WHERE schedule_revision_id=? ORDER BY CASE severity WHEN 'blocking' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END,source_page, id", (revision_id,)
            )]
            runs = [dict(row) for row in db.execute(
                "SELECT * FROM verification_runs WHERE schedule_revision_id=? ORDER BY created_at DESC,id DESC", (revision_id,)
            )]
            for run in runs:
                run["summary"] = json.loads(run["summary_json"])
        return self.send_json({"project": dict(project), "revisions": revisions, "revision_id": revision_id, "doors": doors, "sets": sets, "issues": issues, "runs": runs})

    @staticmethod
    def _set_items(db, set_id):
        rows = db.execute("SELECT * FROM scheduled_items WHERE hardware_set_id=? ORDER BY source_page,source_row_number", (set_id,)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["matches"] = []
            for match in db.execute(
                "SELECT m.id AS match_id,m.product_id,m.match_basis,m.review_status,m.match_rank,m.reviewer_notes,p.* "
                "FROM product_matches m JOIN products p ON p.id=m.product_id WHERE m.scheduled_item_id=? "
                "ORDER BY m.review_status='confirmed' DESC,m.match_rank,p.manufacturer,p.model",
                (row["id"],),
            ).fetchall():
                item["matches"].append({
                    "id": match["match_id"], "product_id": match["product_id"], "match_basis": match["match_basis"],
                    "review_status": match["review_status"], "match_rank": match["match_rank"],
                    "reviewer_notes": match["reviewer_notes"], "product": product_dict(match),
                })
            result.append(item)
        return result

    def get_verification_run(self, db, run_id):
        run = db.execute("SELECT * FROM verification_runs WHERE id=?", (run_id,)).fetchone()
        if not run:
            return self.send_json({"error": "Verification run not found."}, 404)
        doors = []
        for row in db.execute(
            "SELECT v.*,d.door_number,d.heading_number,d.description,d.source_page FROM verification_run_doors v "
            "JOIN scheduled_doors d ON d.id=v.scheduled_door_id WHERE v.verification_run_id=? ORDER BY d.door_number,d.id", (run_id,)
        ):
            value = dict(row)
            value["product_ids"] = json.loads(value.pop("product_ids_json"))
            value["result"] = json.loads(value.pop("result_json"))
            doors.append(value)
        return self.send_json({"run": {**dict(run), "summary": json.loads(run["summary_json"])}, "doors": doors})

    def get_schedule_pages(self, db, revision_id):
        query = parse_qs(urlparse(self.path).query)
        try:
            page = max(1, int(query.get("page", ["1"])[0]))
        except ValueError:
            return self.send_json({"error": "Page number must be an integer."}, 400)
        row = db.execute("SELECT extracted_text FROM schedule_pages WHERE schedule_revision_id=? AND page_number=?", (revision_id, page)).fetchone()
        if not row:
            return self.send_json({"error": "Schedule page not found."}, 404)
        return self.send_json({"revision_id": revision_id, "page_number": page, "text": row["extracted_text"]})

    def get_schedule_file(self, db, source_id):
        source = db.execute("SELECT local_path,title FROM evidence_sources WHERE id=? AND source_type='hardware_schedule'", (source_id,)).fetchone()
        if not source:
            return self.send_json({"error": "Schedule file not found."}, 404)
        file_path = (SCHEDULE_UPLOAD_DIR / Path(source["local_path"]).name).resolve()
        upload_root = SCHEDULE_UPLOAD_DIR.resolve()
        if not file_path.is_relative_to(upload_root) or not file_path.is_file():
            return self.send_json({"error": "The stored schedule file is unavailable."}, 404)
        return self.send_bytes(file_path.read_bytes(), "application/pdf", file_path.name)

    def import_schedule(self, db, data):
        if not isinstance(data, dict):
            return self.send_json({"error": "Schedule import must be an object."}, 400)
        name = str(data.get("name", "")).strip()
        filename = Path(str(data.get("filename", "schedule.pdf"))).name
        encoded = data.get("file_base64", "")
        if not name or not encoded:
            return self.send_json({"error": "Enter a project name and choose a PDF schedule."}, 400)
        if filename.casefold().endswith(".pdf") is False:
            return self.send_json({"error": "Upload a PDF hardware schedule."}, 400)
        try:
            pdf_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            return self.send_json({"error": "The uploaded PDF data could not be decoded."}, 400)
        if len(pdf_bytes) > 50 * 1024 * 1024:
            return self.send_json({"error": "PDF schedules must be 50 MB or smaller."}, 413)
        if not pdf_bytes.startswith(b"%PDF-"):
            return self.send_json({"error": "The selected file is not a valid PDF."}, 400)
        try:
            extracted = extract_schedule(pdf_bytes)
        except Exception as error:
            return self.send_json({"error": f"Could not read this PDF: {error}"}, 400)
        if len(extracted["pages"]) > 2000:
            return self.send_json({"error": "Schedules over 2,000 pages are not supported by this local importer."}, 413)

        digest = hashlib.sha256(pdf_bytes).hexdigest()
        SCHEDULE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        relative_path = Path("data") / "schedules" / f"{digest}.pdf"
        target = SCHEDULE_UPLOAD_DIR / relative_path.name
        if not target.exists():
            target.write_bytes(pdf_bytes)
        project_code = str(data.get("project_code", "")).strip()
        schedule_number = str(data.get("schedule_number", "")).strip()
        revision_label = str(data.get("revision_label", "")).strip() or "Unlabeled revision"
        project_cur = db.execute(
            "INSERT INTO projects(project_code,name,client_name,site_address) VALUES (?,?,?,?)",
            (project_code, name, str(data.get("client_name", "")).strip(), str(data.get("site_address", "")).strip()),
        )
        project_id = project_cur.lastrowid
        metadata = {"page_count": len(extracted["pages"]), "original_filename": filename, "parser": "text-first-reviewed-v1"}
        source_cur = db.execute(
            "INSERT INTO evidence_sources(project_id,source_type,title,local_path,document_sha256,revision_label,metadata_json) VALUES (?,'hardware_schedule',?,?,?,?,?)",
            (project_id, filename, relative_path.as_posix(), digest, revision_label, json.dumps(metadata)),
        )
        source_id = source_cur.lastrowid
        revision_cur = db.execute(
            "INSERT INTO schedule_revisions(project_id,schedule_number,revision_label,evidence_source_id,status,parser_name,parser_version,notes) VALUES (?,?,?,?,'under_review','generic_pdf_text','1',?)",
            (project_id, schedule_number, revision_label, source_id, "Text extraction is heuristic. Review the original PDF, extracted rows, and flagged fields before relying on results."),
        )
        revision_id = revision_cur.lastrowid
        db.executemany(
            "INSERT INTO schedule_pages(schedule_revision_id,page_number,extracted_text) VALUES (?,?,?)",
            [(revision_id, page["page_number"], page["text"]) for page in extracted["pages"]],
        )
        set_ids = {}
        for set_row in extracted["sets"]:
            cur = db.execute(
                "INSERT INTO hardware_sets(schedule_revision_id,set_code,description,source_start_page,source_end_page,source_notes,raw_source_text) VALUES (?,?,?,?,?,?,?)",
                (revision_id, set_row["set_code"], set_row["description"], set_row["start_page"], set_row["end_page"], set_row["notes"], set_row["description"]),
            )
            set_ids[set_row["set_code"].casefold()] = cur.lastrowid
        door_ids = {}
        for door in extracted["doors"]:
            cursor = db.execute(
                "INSERT OR IGNORE INTO scheduled_doors(schedule_revision_id,source_row_number,door_number,heading_number,description,hand,raw_source_text,source_page) VALUES (?,?,?,?,?,?,?,?)",
                (revision_id, door["source_row_number"], door["door_number"], door["heading_number"], door["description"], "", door["raw"], door["page"]),
            )
            door_id = cursor.lastrowid
            if not door_id:
                match = db.execute("SELECT id FROM scheduled_doors WHERE schedule_revision_id=? AND source_row_number=?", (revision_id, door["source_row_number"])).fetchone()
                door_id = match["id"]
            door_ids[door_id] = door
            set_id = set_ids.get(door["heading_number"].casefold()) if door["heading_number"] else None
            if set_id:
                db.execute("INSERT OR IGNORE INTO door_set_assignments(scheduled_door_id,hardware_set_id,source_page,raw_source_text) VALUES (?,?,?,?)", (door_id, set_id, door["page"], door["raw"]))
        for item in extracted["items"]:
            set_id = set_ids.get(item["set_code"].casefold())
            if not set_id:
                continue
            cur = db.execute(
                "INSERT OR IGNORE INTO scheduled_items(hardware_set_id,source_row_number,quantity_for_heading,units,sku,product_text,description_text,source_page,raw_source_text) VALUES (?,?,?,?,?,?,?,?,?)",
                (set_id, item["source_row_number"], item["quantity"], item["units"], item["sku"], item["description"], item["description"], item["page"], item["raw"]),
            )
            item_id = cur.lastrowid
            if not item_id:
                row = db.execute("SELECT id FROM scheduled_items WHERE hardware_set_id=? AND source_row_number=?", (set_id, item["source_row_number"])).fetchone()
                item_id = row["id"]
            for product in db.execute("SELECT id,model FROM products WHERE active=1 ORDER BY model"):
                model = str(product["model"]).strip()
                if len(model) < 4 or model.casefold() not in item["raw"].casefold():
                    continue
                db.execute(
                    "INSERT OR IGNORE INTO product_matches(scheduled_item_id,product_id,match_basis,review_status,match_rank,reviewer_notes) VALUES (?,?,'exact_model','candidate',1,'Automatic text match; confirm against schedule and manufacturer source.')",
                    (item_id, product["id"]),
                )
        for issue in extracted["issues"]:
            db.execute(
                "INSERT INTO import_review_issues(schedule_revision_id,issue_code,severity,message,source_page) VALUES (?,?,?,?,?)",
                (revision_id, issue["code"], issue["severity"], issue["message"], issue["page"]),
            )
        if extracted["doors"] and not any(door["heading_number"] for door in extracted["doors"]):
            db.execute(
                "INSERT INTO import_review_issues(schedule_revision_id,issue_code,severity,message) VALUES (?,'door_set_assignments_not_recognized','warning',?)",
                (revision_id, "Door rows were found but their hardware-set assignments were not confidently detected. Review assignments against the source schedule."),
            )
        return self.send_json({
            "project_id": project_id, "revision_id": revision_id, "source_id": source_id,
            "counts": {"pages": len(extracted["pages"]), "doors": len(extracted["doors"]), "sets": len(extracted["sets"]), "items": len(extracted["items"]), "review_issues": len(extracted["issues"])},
            "message": "Schedule imported for review. Verify extracted rows and matches against the original PDF before running checks.",
        }, 201)

    def add_project_door(self, db, data):
        project_id = data.get("project_id")
        revision = db.execute("SELECT id FROM schedule_revisions WHERE project_id=? ORDER BY imported_at DESC,id DESC LIMIT 1", (project_id,)).fetchone()
        if not revision:
            return self.send_json({"error": "Import a schedule before adding doors."}, 404)
        door_number = str(data.get("door_number", "")).strip()
        if not door_number:
            return self.send_json({"error": "Enter a door number."}, 400)
        set_code = str(data.get("heading_number", "")).strip()
        set_row = db.execute("SELECT id FROM hardware_sets WHERE schedule_revision_id=? AND set_code=? ORDER BY occurrence_number LIMIT 1", (revision["id"], set_code)).fetchone() if set_code else None
        if set_code and not set_row:
            return self.send_json({"error": "Create or choose a hardware set before assigning it to a door."}, 400)
        cur = db.execute(
            "INSERT INTO scheduled_doors(schedule_revision_id,source_row_number,door_number,heading_number,description,hand,raw_source_text,source_page) VALUES (?,?,?,?,?,?,?,?)",
            (revision["id"], -int(db.execute("SELECT COUNT(*)+1 FROM scheduled_doors WHERE schedule_revision_id=?", (revision["id"],)).fetchone()[0]), door_number, set_code, str(data.get("description", "")).strip(), str(data.get("hand", "")).strip(), "Manually added during schedule review.", 1),
        )
        if set_row:
            db.execute("INSERT INTO door_set_assignments(scheduled_door_id,hardware_set_id,raw_source_text) VALUES (?,?,?)", (cur.lastrowid, set_row["id"], "Manually assigned during schedule review."))
        return self.send_json({"id": cur.lastrowid, "door_number": door_number}, 201)

    def add_project_set(self, db, data):
        project_id = data.get("project_id")
        revision = db.execute("SELECT id FROM schedule_revisions WHERE project_id=? ORDER BY imported_at DESC,id DESC LIMIT 1", (project_id,)).fetchone()
        code = str(data.get("set_code", "")).strip()
        if not revision or not code:
            return self.send_json({"error": "Import a schedule and enter a hardware-set code."}, 400)
        try:
            cur = db.execute("INSERT INTO hardware_sets(schedule_revision_id,set_code,description,source_notes) VALUES (?,?,?,?)", (revision["id"], code, str(data.get("description", "")).strip(), "Manually added during schedule review."))
        except sqlite3.IntegrityError:
            return self.send_json({"error": "That hardware-set code already exists in this revision."}, 409)
        return self.send_json({"id": cur.lastrowid, "set_code": code}, 201)

    def add_schedule_item(self, db, set_id, data):
        hardware_set = db.execute("SELECT id FROM hardware_sets WHERE id=?", (set_id,)).fetchone()
        product_text = str(data.get("product_text", "")).strip()
        if not hardware_set or not product_text:
            return self.send_json({"error": "Choose a hardware set and enter the scheduled item text."}, 400)
        try:
            quantity = float(data.get("quantity", 1))
            source_page = max(1, int(data.get("source_page", 1) or 1))
        except (TypeError, ValueError):
            return self.send_json({"error": "Enter a valid quantity and source page."}, 400)
        if quantity <= 0:
            return self.send_json({"error": "Quantity must be greater than zero."}, 400)
        row_number = -(db.execute(
            "SELECT COUNT(*)+1 FROM scheduled_items WHERE hardware_set_id=? AND source_row_number<0", (set_id,)
        ).fetchone()[0])
        cur = db.execute(
            "INSERT INTO scheduled_items(hardware_set_id,source_row_number,quantity_for_heading,units,sku,product_text,description_text,source_page,raw_source_text) VALUES (?,?,?,?,?,?,?,?,?)",
            (set_id, row_number, quantity, str(data.get("units", "EA")).strip() or "EA", str(data.get("sku", "")).strip(), product_text, product_text, source_page, "Manually added during schedule review."),
        )
        return self.send_json({"id": cur.lastrowid}, 201)

    def save_schedule_match(self, db, data):
        try:
            item_id, product_id = int(data.get("scheduled_item_id")), int(data.get("product_id"))
        except (TypeError, ValueError):
            return self.send_json({"error": "Choose a scheduled item and catalog product."}, 400)
        status = data.get("review_status", "confirmed")
        if status not in {"candidate", "confirmed", "rejected"}:
            return self.send_json({"error": "Choose candidate, confirmed, or rejected."}, 400)
        if not db.execute("SELECT 1 FROM scheduled_items WHERE id=?", (item_id,)).fetchone() or not db.execute("SELECT 1 FROM products WHERE id=? AND active=1", (product_id,)).fetchone():
            return self.send_json({"error": "The scheduled item or catalog product was not found."}, 404)
        try:
            if status == "confirmed":
                db.execute("UPDATE product_matches SET review_status='rejected',reviewer_notes='Replaced by a newer confirmed match.',reviewed_at=CURRENT_TIMESTAMP WHERE scheduled_item_id=? AND review_status='confirmed' AND product_id<>?", (item_id, product_id))
            db.execute(
                "INSERT INTO product_matches(scheduled_item_id,product_id,match_basis,review_status,reviewer_notes,reviewed_at) VALUES (?,?, 'manual_candidate',?,?,CURRENT_TIMESTAMP) "
                "ON CONFLICT(scheduled_item_id,product_id) DO UPDATE SET review_status=excluded.review_status,reviewer_notes=excluded.reviewer_notes,reviewed_at=CURRENT_TIMESTAMP",
                (item_id, product_id, status, str(data.get("reviewer_notes", "")).strip()),
            )
        except sqlite3.IntegrityError:
            return self.send_json({"error": "Another catalog product is already confirmed for this scheduled line."}, 409)
        return self.send_json({"saved": True, "review_status": status})

    def verify_project(self, db, project_id, data):
        project = db.execute("SELECT id FROM projects WHERE id=?", (project_id,)).fetchone()
        revision = db.execute("SELECT id FROM schedule_revisions WHERE project_id=? ORDER BY imported_at DESC,id DESC LIMIT 1", (project_id,)).fetchone()
        if not project or not revision:
            return self.send_json({"error": "Project or imported schedule was not found."}, 404)
        doors = db.execute("SELECT * FROM scheduled_doors WHERE schedule_revision_id=? ORDER BY door_number,id", (revision["id"],)).fetchall()
        if not doors:
            return self.send_json({"error": "Add or extract door rows before running verification."}, 400)
        run_cur = db.execute("INSERT INTO verification_runs(project_id,schedule_revision_id,run_name) VALUES (?,?,?)", (project_id, revision["id"], str(data.get("run_name", "")).strip()))
        run_id = run_cur.lastrowid
        counts = {}
        for door in doors:
            set_ids = [row["hardware_set_id"] for row in db.execute("SELECT hardware_set_id FROM door_set_assignments WHERE scheduled_door_id=?", (door["id"],))]
            confirmed_ids = []
            if set_ids:
                placeholders = ",".join("?" for _ in set_ids)
                confirmed_ids = [row["product_id"] for row in db.execute(
                    f"SELECT DISTINCT m.product_id FROM scheduled_items i JOIN product_matches m ON m.scheduled_item_id=i.id WHERE i.hardware_set_id IN ({placeholders}) AND m.review_status='confirmed' ORDER BY m.product_id", set_ids
                )]
            opening = {}
            if door["leaf_width_1_mm"] is not None:
                opening["width_in"] = round(door["leaf_width_1_mm"] / 25.4, 2)
            if door["height_mm"] is not None:
                opening["height_in"] = round(door["height_mm"] / 25.4, 2)
            if door["door_material"]:
                opening["door_material"] = door["door_material"]
            if door["frame_material"]:
                opening["frame_material"] = door["frame_material"]
            if door["fire_rating"]:
                opening["fire_rated"] = "yes"
            if len(confirmed_ids) >= 2:
                harness = _JsonHarness()
                Handler.check_assembly(harness, {"product_ids": confirmed_ids, "opening": opening})
                result = harness.response[1]
            else:
                result = {"status": "unverified", "message": "At least two scheduled lines need confirmed catalog matches before this door can be checked.", "estimate": {"score": None, "confidence": 0, "verdict": "unverified", "checks_in_average": 0}, "findings": [], "subset_checks": []}
            status = result.get("status", "unverified")
            counts[status] = counts.get(status, 0) + 1
            db.execute(
                "INSERT INTO verification_run_doors(verification_run_id,scheduled_door_id,product_ids_json,result_json) VALUES (?,?,?,?)",
                (run_id, door["id"], json.dumps(confirmed_ids), json.dumps(result)),
            )
        summary = {"door_count": len(doors), "status_counts": counts}
        db.execute("UPDATE verification_runs SET summary_json=? WHERE id=?", (json.dumps(summary), run_id))
        return self.send_json({"run_id": run_id, "summary": summary}, 201)

    def import_evidence_bundle(self, db, data):
        if not isinstance(data, dict):
            return self.send_json({"error": "Import must be a JSON object."}, 400)
        fields = {
            "compatibilityRules": "rules",
            "assertions": "assertions",
            "researchNotes": "research notes",
        }
        if not any(key in data for key in fields):
            return self.send_json({"error": "Include compatibilityRules, assertions, and/or researchNotes arrays."}, 400)
        errors, created, updated = [], {key: 0 for key in fields}, {key: 0 for key in fields}
        for key, label in fields.items():
            rows = data.get(key, [])
            if not isinstance(rows, list):
                errors.append({"section": key, "row": 0, "error": f"{label} must be an array."})
                continue
            for index, item in enumerate(rows, 1):
                try:
                    if not isinstance(item, dict):
                        raise ValueError("Each row must be a JSON object.")
                    if key == "compatibilityRules":
                        name = str(item.get("name", "")).strip()
                        category_a, category_b = item.get("category_a"), item.get("category_b")
                        comparison = item.get("comparison")
                        pass_outcome, fail_outcome = item.get("pass_outcome", "conditional"), item.get("fail_outcome", "conditional")
                        status = item.get("evidence_status", "research_lead")
                        source_title, source_url = str(item.get("source_title", "")).strip(), str(item.get("source_url", "")).strip()
                        rationale = str(item.get("rationale", "")).strip()
                        if not name: raise ValueError("Rule name is required.")
                        if category_a not in PRODUCT_CATEGORIES or category_b not in PRODUCT_CATEGORIES: raise ValueError("Both categories must be valid product categories.")
                        if comparison not in {"equals", "not_equals", "less_or_equal", "greater_or_equal", "contains"}: raise ValueError("Unsupported comparison.")
                        if pass_outcome not in {"compatible", "incompatible", "conditional"} or fail_outcome not in {"compatible", "incompatible", "conditional"}: raise ValueError("Pass/fail outcomes must be compatible, incompatible, or conditional.")
                        if status not in EVIDENCE_STATUSES: raise ValueError("Unknown evidence_status.")
                        if status != "research_lead" and not source_url: raise ValueError("Verified rules need a source_url.")
                        values = (category_a, category_b, str(item.get("spec_a", "")).strip(), comparison, str(item.get("spec_b", "")).strip(), pass_outcome, fail_outcome, rationale, source_title, source_url, status)
                        existing = db.execute("SELECT id FROM compatibility_rules WHERE name=?", (name,)).fetchone()
                        if existing:
                            db.execute("UPDATE compatibility_rules SET category_a=?,category_b=?,spec_a=?,comparison=?,spec_b=?,pass_outcome=?,fail_outcome=?,rationale=?,source_title=?,source_url=?,evidence_status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (*values, existing["id"]))
                            updated[key] += 1
                        else:
                            db.execute("INSERT INTO compatibility_rules(name,category_a,category_b,spec_a,comparison,spec_b,pass_outcome,fail_outcome,rationale,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (name, *values))
                            created[key] += 1
                    elif key == "assertions":
                        references = item.get("products", [])
                        if not isinstance(references, list) or len(references) < 2: raise ValueError("An assertion needs at least two product references.")
                        product_ids = []
                        for reference in references:
                            if not isinstance(reference, dict): raise ValueError("Each product reference needs category, manufacturer, and model.")
                            category, manufacturer, model = reference.get("category"), str(reference.get("manufacturer", "")).strip(), str(reference.get("model", "")).strip()
                            if category not in PRODUCT_CATEGORIES or not manufacturer or not model: raise ValueError("Each product reference needs a valid category, manufacturer, and model.")
                            match = db.execute("SELECT id FROM products WHERE active=1 AND category=? AND manufacturer=? AND model=?", (category, manufacturer, model)).fetchone()
                            if not match: raise ValueError(f"Product not found in the active catalog: {manufacturer} {model} ({category}).")
                            product_ids.append(match["id"])
                        normalized = normalized_ids(product_ids)
                        if len(normalized) < 2: raise ValueError("An assertion needs two distinct catalog products.")
                        outcome, status = item.get("outcome"), item.get("evidence_status", "research_lead")
                        conditions = item.get("conditions", {})
                        source_title, source_url = str(item.get("source_title", "")).strip(), str(item.get("source_url", "")).strip()
                        if outcome not in {"compatible", "incompatible", "conditional"}: raise ValueError("Invalid assertion outcome.")
                        if status not in EVIDENCE_STATUSES: raise ValueError("Unknown evidence_status.")
                        if not isinstance(conditions, dict): raise ValueError("conditions must be a JSON object.")
                        if status != "research_lead" and not source_url: raise ValueError("Verified assertions need a source_url.")
                        product_json = json.dumps(normalized, separators=(",", ":"))
                        conditions_json = json.dumps(conditions, sort_keys=True, separators=(",", ":"))
                        values = (outcome, conditions_json, str(item.get("rationale", "")).strip(), source_title, source_url, status)
                        existing = db.execute("SELECT id FROM compatibility_assertions WHERE product_ids=? AND conditions=?", (product_json, conditions_json)).fetchone()
                        if existing:
                            db.execute("UPDATE compatibility_assertions SET outcome=?,conditions=?,rationale=?,source_title=?,source_url=?,evidence_status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (*values, existing["id"]))
                            updated[key] += 1
                        else:
                            db.execute("INSERT INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,?,?)", (product_json, *values))
                            created[key] += 1
                    else:
                        topic = str(item.get("topic", "")).strip()
                        components = str(item.get("related_components", "")).strip()
                        guidance = str(item.get("guidance", "")).strip()
                        source_title, source_url = str(item.get("source_title", "")).strip(), str(item.get("source_url", "")).strip()
                        status = item.get("evidence_status", "research_lead")
                        if not topic or not guidance or not source_title or not source_url: raise ValueError("Research notes require topic, guidance, source_title, and source_url.")
                        if status not in EVIDENCE_STATUSES: raise ValueError("Unknown evidence_status.")
                        existing = db.execute("SELECT id FROM research_notes WHERE topic=? AND source_url=?", (topic, source_url)).fetchone()
                        if existing:
                            db.execute("UPDATE research_notes SET related_components=?,guidance=?,source_title=?,evidence_status=? WHERE id=?", (components, guidance, source_title, status, existing["id"]))
                            updated[key] += 1
                        else:
                            db.execute("INSERT INTO research_notes(topic,related_components,guidance,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,?)", (topic, components, guidance, source_title, source_url, status))
                            created[key] += 1
                except (ValueError, sqlite3.IntegrityError) as error:
                    errors.append({"section": key, "row": index, "error": str(error)})
        result = {"created": created, "updated": updated, "errors": errors}
        return self.send_json(result, 200 if not errors else 207)

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
        opening = data.get("opening", {}) if isinstance(data.get("opening", {}), dict) else {}
        if len(product_ids) < 1 or (len(product_ids) < 2 and not opening):
            return self.send_json({"error": "Choose two products for pair checks, or select one product and enter opening details to check fit."}, 400)
        with connect() as db:
            products = [product_dict(row) for row in db.execute(
                f"SELECT * FROM products WHERE active=1 AND id IN ({','.join('?' for _ in product_ids)}) ORDER BY category,manufacturer,model",
                product_ids,
            )]
            if len(products) != len(product_ids):
                return self.send_json({"error": "One or more selected products were not found."}, 404)
            context = data.get("context", {}) if isinstance(data.get("context", {}), dict) else {}
            context = {**opening, **context}
            findings = []
            pair_estimates = []
            tuple_assertions = []
            exact_applies = False
            selected_ids = set(product_ids)
            products_by_id = {product["id"]: product for product in products}
            for row in db.execute("SELECT * FROM compatibility_assertions ORDER BY updated_at DESC"):
                candidate = assertion_dict(row)
                candidate_ids = set(candidate["product_ids"])
                if len(candidate_ids) < 3 or not candidate_ids.issubset(selected_ids):
                    continue
                tuple_products = [products_by_id[product_id] for product_id in candidate_ids]
                conditions_match = all(context.get(key) == value for key, value in candidate["conditions"].items())
                products_documented = all(trusted_product_record(product) for product in tuple_products)
                if not trusted_evidence(candidate["evidence_status"]) or not conditions_match or not products_documented:
                    continue
                tuple_assertions.append(candidate)
                findings.append({
                    "status": candidate["outcome"],
                    "finding_type": "assembly_tuple",
                    "rationale": candidate["rationale"],
                    "source_title": candidate["source_title"],
                    "source_url": candidate["source_url"],
                    "product_ids": candidate["product_ids"],
                })
                if candidate_ids == selected_ids and not exact_applies:
                    exact_applies = True
                    assertion = candidate
            if exact_applies:
                # An exact whole-assembly tuple subsumes its smaller documented
                # tuples. Keep the report focused on the assertion for the
                # complete selected set instead of counting the subset twice.
                tuple_assertions = [assertion]
                findings = [finding for finding in findings if finding.get("finding_type") != "assembly_tuple"]
                findings.append({
                    "status": assertion["outcome"],
                    "finding_type": "assembly_tuple",
                    "rationale": assertion["rationale"],
                    "source_title": assertion["source_title"],
                    "source_url": assertion["source_url"],
                    "product_ids": assertion["product_ids"],
                })
            subset_checks = assembly_subset_checks(db, products, context) if len(products) > 2 else []
            subset_conflicts = [
                check for check in subset_checks
                if check["subset_size"] < len(products)
                and check["status"] == "incompatible"
                and trusted_evidence(check["evidence_status"])
            ]
            for check in subset_conflicts:
                findings.append({
                    "status": check["status"],
                    "finding_type": "subset_assertion_conflict",
                    "rationale": check["rationale"],
                    "source_title": check["source_title"],
                    "source_url": check["source_url"],
                    "product_ids": check["product_ids"],
                    "evidence_status": check["evidence_status"],
                })
            if len(products) == 2:
                for left_index, product_a in enumerate(products):
                    for product_b in products[left_index + 1:]:
                        if not pair_is_applicable(product_a, product_b, db):
                            continue
                        evaluation = pair_evaluation(db, product_a, product_b, context)
                        findings.append({"product_a": product_a, "product_b": product_b, **evaluation})
                        pair_estimates.append(pair_estimate(db, product_a, product_b, context))
            findings.extend(
                {**finding, "finding_type": finding.get("finding_type", "opening_fit")}
                for finding in opening_fit_findings(products, opening)
            )
            if not exact_applies:
                findings.extend(power_path_findings(products))
            if len(products) == 1 and not findings:
                findings.append({"status": "unverified", "product_a": products[0], "rationale": "No opening-fit constraint is documented for this selected product category."})
            if not all(trusted_evidence(product["evidence_status"]) for product in products):
                findings.append({"status": "unverified", "rationale": "At least one selected product is still a research lead; verify its exact model and specifications from a primary source."})
            statuses = [finding["status"] for finding in findings]
            status = "incompatible" if "incompatible" in statuses else "conditional" if "conditional" in statuses else "compatible" if statuses and all(value == "compatible" for value in statuses) else "unverified"
            messages = {
                "compatible": "All applicable checks passed using sourced product data.",
                "incompatible": "At least one selected product pair has a documented conflict.",
                "conditional": "A documented condition must be satisfied before this combination can be used.",
                "unverified": "Some selected products or interactions do not have enough verified evidence yet.",
            }
            assembly_level_findings = [
                finding for finding in findings
                if (finding.get("product_a") and not finding.get("product_b"))
                or finding.get("finding_type") == "power_path"
                or finding.get("finding_type") == "subset_assertion_conflict"
            ]
            estimate_assertions = tuple_assertions if exact_applies else []
            if exact_applies:
                # The exact whole-group assertion is the primary assembly
                # result. Do not dilute it with unresolved opening-fit data;
                # independently documented conflicts still take precedence.
                independent_conflicts = [
                    finding for finding in findings
                    if finding.get("status") == "incompatible"
                    and finding.get("finding_type") != "assembly_tuple"
                ]
                estimate = assembly_estimate([], independent_conflicts, estimate_assertions)
            else:
                estimate = assembly_estimate(pair_estimates, assembly_level_findings, estimate_assertions)
            if len(products) > 2 and not exact_applies and status == "compatible":
                status = "unverified"
            if len(products) > 2 and not exact_applies and estimate.get("verdict") in {"compatible", "likely_compatible"}:
                estimate["verdict"] = "unverified"
                estimate["message"] = "No exact assertion covers the complete selected assembly; evidence for smaller subsets does not prove the full combination."
            if estimate.get("score") is not None:
                status = estimate["verdict"]
            return self.send_json({"status": status, "message": estimate["message"] if estimate.get("score") is not None else messages[status], "estimate": estimate, "assertion": assertion if exact_applies else None, "products": products, "findings": findings, "subset_checks": subset_checks})

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

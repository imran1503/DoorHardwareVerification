"""Source-backed catalog research for the first Belleville schedule set."""
import json


def seed_belleville_set_1_research(db):
    sources = {
        "ed100": ("dormakaba ED100/ED250 SA Installation Instructions", "https://my.dormakaba.com/medias/DL4615-006-R012820-ED100-250-SA-Installation-Instructions.pdf?context=bWFzdGVyfGltYWdlc3wxODkxNzc2N3xhcHBsaWNhdGlvbi9wZGZ8aW1hZ2VzL2g3My9oYjMvODk0MzU0OTQ0ODIyMi5wZGZ8NTE1MzdmMDFhMTBiZThiZTQwNmQyZDNkOGI4YTBmNjgyOTMwNzM4MjQxNTkxMTJlZmZmMGNhYzBhOWFlZDNkOQ"),
        "camden": ("Camden CM-25, CM-26CB and CM-35 Series Technical Specification", "https://www.camdencontrols.com/pipelines/resource/10282_CM_TX_99_Manual_Eng_Rev3.pdf"),
        "dorma7400": ("dormakaba 7400 Series Templates and Instructions", "https://dhwsupport.dormakaba.com/hc/en-us/articles/360046576974-7400-Series-Templates-and-Instructions"),
        "abh": ("ABH 1000 Series Overhead Holder Product Literature", "https://www.abhmfg.com/content/documents/0002561_abh_pl_14_v12.pdf"),
        "abh_chart": ("ABH Closer and Overhead Holder Compatibility Chart", "https://www.abhmfg.com/content/documents/0000107_overhead_holder_compatibility_chart_with_other_manufacturers_closers.pdf"),
        "hinge": ("dormakaba 661HD Full Mortise Aluminum Geared Hinge Templates", "https://dhwsupport.dormakaba.com/hc/en-us/articles/202065543-661HD-Full-Mortise-Aluminum-Geared-Hinges"),
        "sweep": ("K.N. Crowder W-24S Sweep Cut Sheet", "https://www.kncrowder.com/web/uploads/products/docs/W-24S.pdf"),
        "threshold": ("K.N. Crowder CT-45 Thermal Break Threshold Cut Sheet", "https://www.kncrowder.com/web/uploads/products/docs/CT-45_R.pdf"),
        "report": ("Belleville Set 1 Manufacturer Source Comparison", "/evidence/belleville-set-1-research.md#findings"),
    }
    source_ids = {}
    for key, (title, url) in sources.items():
        source_type = "other" if key == "report" else "manufacturer_document"
        if key == "report":
            db.execute("UPDATE evidence_sources SET source_type='other' WHERE title=? AND source_url=?", (title, url))
        row = db.execute("SELECT id FROM evidence_sources WHERE source_type=? AND title=? AND source_url=? ORDER BY id LIMIT 1", (source_type, title, url)).fetchone()
        if not row:
            db.execute("INSERT INTO evidence_sources(source_type,title,source_url,metadata_json) VALUES (?,?,?, '{}')", (source_type, title, url))
            row = db.execute("SELECT id FROM evidence_sources WHERE source_type=? AND title=? AND source_url=? ORDER BY id DESC LIMIT 1", (source_type, title, url)).fetchone()
        source_ids[key] = row["id"]

    products = [
        ("activation_device", "Camden Controls", "CM-35N/4", "Camden CM-35N/4 narrow activation switch", {"record_scope":"exact_model","contact_type":"normally_open_spst","switch_action":"momentary","contact_rating":{"current_a":3,"voltage_vdc":30},"mounting":"narrow jamb plate","schedule_token":"630CM-35N/4"}, "camden", "CM-35N/4 model listing and series specifications", "Momentary N/O SPST contact, rated 3 A at 30 VDC."),
        ("hinge", "dormakaba", "661HD", "dormakaba 661HD full-mortise aluminum geared continuous hinge", {"record_scope":"exact_model","hinge_type":"full_mortise_aluminum_geared_continuous","application":"flush door and frame","schedule_token":"628661HD","scheduled_length_mm":2108,"scheduled_length_in":83.0,"nominal_leaf_height_in":84,"ce_wiring":False}, "hinge", "661HD template listing and standard size table", "661HD is listed separately from the CE variant; 83-inch actual length is the standard size for a nominal 84-inch leaf."),
        ("closer", "dormakaba", "7414 ARJ", "dormakaba 7414 ARJ top-jamb door closer", {"record_scope":"exact_model","mounting":"top_jamb","closer_family":"7400","schedule_token":"6897414 ARJ"}, "dorma7400", "7414/7436 ARJ top-jamb templates", "Manufacturer lists 7414 ARJ top-jamb installation templates."),
        ("other", "dormakaba", "BP86", "dormakaba BP86 closer mounting plate", {"record_scope":"exact_model","accessory_type":"closer_mounting_plate","supported_models":["7414 ARJ","7436 ARJ"],"mounting":"top_jamb","schedule_token":"689BP86"}, "dorma7400", "Template 08280403", "The 7414/7436 ARJ top-jamb template lists BP86 as an available plate configuration."),
        ("door_stop", "Architectural Builders Hardware Mfg. Inc.", "1013", "ABH 1013 1000 Series concealed overhead holder", {"record_scope":"exact_model","series":"1000","function":"hold_open","mounting":"concealed","frame_opening_range_in":[36,39.9375],"hinges_assumed":["butt_hinges","offset_pivots"],"schedule_token":"6301013"}, "abh", "1000 Series model/function and opening-width table", "1000 Series table identifies 1013 as the hold-open model for 36–39 15/16 inch openings with butt hinges or offset pivots."),
        ("door_seal", "K.N. Crowder", "W-24S", "K.N. Crowder W-24S brush door sweep", {"record_scope":"exact_model","seal_type":"nylon_brush_sweep","standard_finish":"clear_anodized","max_length_in":144,"schedule_token":"628W-24S","scheduled_length_mm":965}, "sweep", "W-24S cut sheet", "Clear-anodized aluminum sweep with 1-inch nylon brush; maximum length 144 inches."),
        ("threshold", "K.N. Crowder", "CT-45", "K.N. Crowder CT-45 1/2-inch thermal break threshold", {"record_scope":"exact_model","threshold_type":"thermal_break","rise_in":0.5,"insert_included":True,"max_length_in":192,"schedule_token":"627CT-45","scheduled_length_mm":1930}, "threshold", "CT-45 cut sheet", "1/2-inch thermal-break threshold with insert included; maximum length 192 inches."),
    ]
    product_ids = {}
    for category, maker, model, name, specs, source, locator, excerpt in products:
        title, url = sources[source]
        db.execute("INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,'manufacturer_document',?)", (category,maker,model,name,json.dumps(specs,separators=(",",":")),title,url,"Manufacturer documentation supports listed model facts; schedule finish/code and opening-specific fit remain for review."))
        product_id = db.execute("SELECT id FROM products WHERE category=? AND manufacturer=? AND model=?", (category,maker,model)).fetchone()["id"]
        product_ids[model] = product_id
        db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (product_id,source_ids[source],locator,excerpt))

    candidate_patterns = [("661HD", "%628661HD%"), ("7414 ARJ", "%7414 ARJ%"), ("BP86", "%689BP86%"), ("1013", "%6301013%"), ("W-24S", "%W-24S 965MM%"), ("CT-45", "%CT-45 1930MM%"), ("CM-35N/4", "%CM-35N/4%")]
    for model, pattern in candidate_patterns:
        for item in db.execute("SELECT id FROM scheduled_items WHERE product_text LIKE ?", (pattern,)):
            db.execute("INSERT OR IGNORE INTO product_matches(scheduled_item_id,product_id,match_basis,review_status,match_rank,reviewer_notes) VALUES (?,?,'exact_model','candidate',1,'Research candidate: exact model token found; reviewer must confirm schedule suffix, finish and configuration.')", (item["id"], product_ids[model]))
            match_id = db.execute("SELECT id FROM product_matches WHERE scheduled_item_id=? AND product_id=?", (item["id"], product_ids[model])).fetchone()["id"]
            source_key = next(product[5] for product in products if product[2] == model)
            db.execute("INSERT OR IGNORE INTO product_match_evidence(product_match_id,evidence_source_id,locator,excerpt) VALUES (?,?,?,?)", (match_id, source_ids[source_key], "Manufacturer model listing", "Manufacturer source identifies the exact product model; schedule finish and suffix remain review items."))

    ed100 = db.execute("SELECT id,source_url,source_title FROM products WHERE category='automatic_operator' AND manufacturer='dormakaba' AND model='ED100'").fetchone()
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (ed100["id"],source_ids["ed100"],"Technical data §6.1; activation inputs X4","115 VAC ±10%, 6.6 A max; X4 interior/exterior N.O. activation contacts; 24 VDC accessory output up to 1.5 A."))

    ed100_id = db.execute("SELECT id FROM products WHERE category='automatic_operator' AND manufacturer='dormakaba' AND model='ED100'").fetchone()["id"]
    interface_ids = sorted([product_ids["CM-35N/4"], ed100_id])
    interface_rationale = ("Limited interface finding: Camden documents CM-35N/4 as a momentary normally-open SPST contact (3 A at 30 VDC); dormakaba documents ED100 X4 interior/exterior activation inputs as normally-open contacts. This supports using the switch contact as an activation input when wired to X4 per the ED100 instructions. It does not establish complete assembly compatibility, operator mode, door fit, accessibility/code compliance, or whole-door operation.")
    db.execute("INSERT OR IGNORE INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?,'compatible','{}',?,?,?,'manufacturer_document')", (json.dumps(interface_ids,separators=(",",":")),interface_rationale,"Camden and dormakaba manufacturer interface comparison — Belleville Set 1",sources["report"][1]))

    closer_plate_ids = sorted([product_ids["7414 ARJ"], product_ids["BP86"]])
    closer_plate_rationale = "dormakaba's 7414/7436 ARJ top-jamb template lists BP86 as an available plate configuration. Use the matching template and verify reveal, header/frame geometry, and installed arm. This finding does not assess clearance against other hardware in the opening."
    db.execute("INSERT OR IGNORE INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?,'compatible','{}',?,?,?,'manufacturer_document')", (json.dumps(closer_plate_ids,separators=(",",":")),closer_plate_rationale,sources["dorma7400"][0],sources["dorma7400"][1]))

    warning = "ABH's chart marks a 7400 ARJ top-jamb closer with the 1000 concealed holder as incompatible under stated assumptions: 36-inch door, 90-degree opening, butt hinges. Door 100A is about 38 inches wide and uses a continuous geared hinge, so the row does not prove a universal conflict for this opening. Treat it as an installation hold pending the exact ABH template and combined-layout check."
    db.execute("INSERT OR IGNORE INTO research_notes(topic,related_components,guidance,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,'manufacturer_document')", ("Belleville Set 1: 7414 ARJ closer and ABH 1013 holder interference review",json.dumps(["dormakaba 7414 ARJ","ABH 1013","661HD continuous geared hinge"]),warning,sources["abh_chart"][0],sources["abh_chart"][1]))

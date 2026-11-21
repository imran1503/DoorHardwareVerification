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


def seed_belleville_set_2_research(db):
    """Source-backed catalog research for Belleville Set 2 / door 100B."""
    sources = {
        "cx33": ("Camden CX-33 Advanced Logic Relay product page and R7 manual", "https://www.camdencontrols.com/products/CX_33"),
        "cx33_manual": ("Camden CX-33 Installation Instructions R7", "https://www.camdencontrols.com/products/CX_33"),
        "ed100": ("dormakaba ED100/ED250 SA Installation Instructions", "https://my.dormakaba.com/medias/DL4615-006-R012820-ED100-250-SA-Installation-Instructions.pdf?context=bWFzdGVyfGltYWdlc3wxODkxNzc2N3xhcHBsaWNhdGlvbi9wZGZ8aW1hZ2VzL2g3My9oYjMvODk0MzU0OTQ0ODIyMi5wZGZ8NTE1MzdmMDFhMTBiZThlYjQwNmQyZDNkOGI4YTBmNjgyOTMwNzM4MjQxNTkxMTJlZmZmMGNhYzBhOWFlZDNkOQ"),
        "cm35": ("Camden CM-25, CM-26CB and CM-35 Series Technical Specification", "https://www.camdencontrols.com/pipelines/resource/10282_CM_TX_99_Manual_Eng_Rev3.pdf"),
        "rci9540": ("dormakaba RCI 9540 Recessed Contact/Door Position Switch", "https://www.dormakaba.com/us-en/offering/products/electronic-access-data/power-supplies/rci-9540-recessed-magnetic-contactdoor-position-switch--ka_500302"),
        "rci9540_manual": ("dormakaba RCI 9540 Installation Instructions", "https://my.dormakaba.com/medias/9540-Install-IS9540-R0216-2.pdf?context=bWFzdGVyfHJvb3R8NjYzNzR8YXBwbGljYXRpb24vcGRmfGgxZS9oNDUvODg3NzUxNzU3MDA3OC5wZGZ8ZWJiZDA4YWNmZTM3Y2RlNDg4MWJlNzViMGU3OTM1ZTNjNjQ1NTkwNGFkMzA5MGFiNTY0NWY5MDdmNjY5M2ZkZQ"),
        "rci915": ("dormakaba RCI 915 Passive Infrared Egress Switch", "https://www.dormakaba.com/us-en/offering/products/electronic-access-data/switches/rci-915-passive-infrared--ka_500287"),
        "qed": ("dormakaba QED/QET 100 Series Templates, Instructions and Specifications", "https://dhwsupport.dormakaba.com/hc/en-us/articles/218627567-QED-QET-100-Series-Templates-Instructions-and-Specifications"),
        "qed_faq": ("dormakaba QED 100 Frequently Asked Questions", "https://dhwsupport.dormakaba.com/hc/en-us/articles/204622778-QED-100-FAQ-s"),
        "mlr": ("dormakaba QED 100 Series MLR Installation Instructions", "https://dhwsupport.dormakaba.com/hc/article_attachments/9619472256155"),
        "mullion": ("dormakaba DORMA Removable Mullions", "https://www.dormakaba.com/us-en/offering/routes.products/door-hardware/door-hardware-exit-devices/mullions--do_36522"),
        "mullion_instructions": ("dormakaba Mullion Templates and Instructions", "https://dhwsupport.dormakaba.com/hc/en-us/articles/360049977834-Mullion-Templates-and-Instructions"),
        "qrm": ("dormakaba QRM 100 and 300 Series Mullions Specifications", "https://dhwsupport.dormakaba.com/hc/en-us/articles/218971217-QRM-100-and-300-Series-Mullions-Installation-Instruction-and-Specification"),
        "report": ("Belleville Set 2 Manufacturer Source Comparison", "/evidence/belleville-set-2-research.md#findings"),
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
        ("exit_device", "dormakaba", "QED111", "dormakaba QED100 rim exit device, Hex Dog function", {"record_scope":"product_family_function","function":"rim_hex_dog","available_finish_tokens":["626"],"nominal_device_width_in":48,"field_sizeable_width_in":[36,48],"standard_door_thickness_in":1.75,"schedule_token":"626QED111 8Q00254 STRIKE 1219MM"}, "qed", "QED100 Series template table and FAQ: QED111 rim variant; 48-inch size range and finish listed separately", "Manufacturer lists QED111 as a QED 100 rim variant; QED100 FAQ identifies 626 finish and a 48-inch device field sizeable for 36–48 inch doors."),
        ("mullion", "dormakaba", "1310-8", "DORMA 1310 removable mullion, 8-foot", {"record_scope":"exact_model_family","height_ft":8,"material":"aluminum_or_steel_family_options","schedule_finish_token":"628","schedule_token":"6281310-8 2438MM"}, "mullion", "DORMA Removable Mullions product details", "Manufacturer lists 8-foot or 10-foot removable mullions and finish 628 for aluminum mullions."),
        ("door_contact", "dormakaba RCI", "9540", "RCI 9540 recessed magnetic contact / door position switch", {"record_scope":"exact_model","contact_configuration":"SPDT","loop_type":"open_closed","diameter_mm":19,"max_current_ma":200,"max_voltage_vac_vdc":30,"lead_length_in":12,"wire_awg":22,"schedule_finish":"black","schedule_token":"BLACK 9540 SPDT 19.05MM DIA"}, "rci9540", "9540 product details", "The 9540 is SPDT, 19 mm recessed, 200 mA maximum at 30 VAC/VDC, with 12-inch 22 AWG leads and black finish available."),
        ("request_to_exit", "dormakaba RCI", "915", "RCI 915 passive infrared request-to-exit switch", {"record_scope":"exact_model","technology":"passive_infrared","supply_vdc":[12,24],"max_current_ma_at_24v":38,"relay_outputs":"two Form C","relay_rating_a":2,"relay_rating_vdc":30,"latch_delay_seconds":[2,60],"schedule_token":"915"}, "rci915", "915 product details", "The 915 is a hands-free PIR egress device with field-selectable 12/24 VDC, two Form C relays rated 2 A at 30 VDC, and adjustable 2–60 second latch."),
    ]
    product_ids = {}
    for category, maker, model, name, specs, source, locator, excerpt in products:
        title, url = sources[source]
        db.execute("INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,'manufacturer_document',?)", (category,maker,model,name,json.dumps(specs,separators=(",",":")),title,url,"Catalog record reflects sourced model/family facts; exact ordering code, opening preparation, and complete assembly fit remain subject to review."))
        product_id = db.execute("SELECT id FROM products WHERE category=? AND manufacturer=? AND model=?", (category,maker,model)).fetchone()["id"]
        product_ids[model] = product_id
        db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (product_id,source_ids[source],locator,excerpt))

    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (product_ids["QED111"],source_ids["qed_faq"],"QED 100 FAQ: finishes and width range","QED100 finish 626 is offered; 48-inch devices are field sizeable for 36–48 inch doors."))
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (product_ids["1310-8"],source_ids["mullion_instructions"],"Instruction index entry I-1310","Manufacturer provides a distinct 1310 mullion installation instruction sheet; verify the sheet's strike and exit-device preparation for this opening."))
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'other',?,?)", (product_ids["QED111"],source_ids["qrm"],"QRM100 specification","Manufacturer explicitly identifies QRM100 as pre-prepped for QED100; that fact does not establish that the separately scheduled 1310 mullion is pre-prepped for QED100."))

    # The CX-33 and other products already exist in the live catalog. Attach this batch's manufacturer sources.
    cx33 = db.execute("SELECT id FROM products WHERE category='controller' AND manufacturer='Camden Controls' AND model='CX-33'").fetchone()["id"]
    cm35 = db.execute("SELECT id FROM products WHERE category='activation_device' AND manufacturer='Camden Controls' AND model='CM-35N/4'").fetchone()["id"]
    ed100 = db.execute("SELECT id FROM products WHERE category='automatic_operator' AND manufacturer='dormakaba' AND model='ED100'").fetchone()["id"]
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (cx33,source_ids["cx33"],"CX-33 specification table","Camden identifies four dry and one wet input and three Form C relay outputs; contacts are rated 3 A at 24 VDC."))
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (cx33,source_ids["cx33_manual"],"Programmable Inputs","Dry and wet inputs can be programmed for normally-open or normally-closed contacts; mode changes restore that mode's defaults."))
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'supports_product',?,?)", (ed100,source_ids["ed100"],"Activation inputs X4","X4 interior/exterior activation inputs accept normally-open contacts; the instructions specify the activation wiring and configuration."))

    candidates = [
        ("36201", product_ids["1310-8"], "manufacturer_model", "mullion_instructions", "1310-8 model and 628 finish token align; confirm the selected mullion template and exit-device preparation."),
        ("35002", product_ids["QED111"], "manufacturer_model", "qed", "QED111 model/function and 626 finish align; 1219 mm scheduled device width is nominally 48 inches. Confirm field-sizing and door preparation."),
        ("35120", 206, "exact_model", "mlr", "Existing catalog record matches the scheduled 626QED111-MLR token. Confirm latch-retraction power supply and wiring."),
        ("11024", ed100, "exact_model", "ed100", "Existing catalog record matches ED100 model token; confirm the scheduled SA configuration, arm, hand and header/reveal."),
        ("12100", cx33, "exact_model", "cx33", "Exact CX-33 model token; scheduled wiring and mode are not specified."),
        ("12002", cm35, "exact_model", "cm35", "Exact CM-35N/4 model token; verify actuator wiring and desired operating logic."),
        ("96505", product_ids["9540"], "exact_model", "rci9540", "Exact RCI 9540 model token and SPDT/19.05 mm schedule description; black finish is available from the manufacturer."),
        ("96500", product_ids["915"], "exact_model", "rci915", "Exact RCI 915 model token; the schedule does not provide power or relay wiring."),
    ]
    for sku, product_id, basis, source_key, notes in candidates:
        items = db.execute("SELECT si.id FROM scheduled_items si JOIN hardware_sets hs ON hs.id=si.hardware_set_id WHERE hs.set_code='2' AND si.sku=?", (sku,)).fetchall()
        for item in items:
            db.execute("INSERT OR IGNORE INTO product_matches(scheduled_item_id,product_id,match_basis,review_status,match_rank,reviewer_notes) VALUES (?,?,?,'candidate',1,?)", (item["id"],product_id,basis,notes))
            match_id = db.execute("SELECT id FROM product_matches WHERE scheduled_item_id=? AND product_id=?", (item["id"],product_id)).fetchone()["id"]
            db.execute("INSERT OR IGNORE INTO product_match_evidence(product_match_id,evidence_source_id,locator,excerpt) VALUES (?,?,?,?)", (match_id,source_ids[source_key],"Manufacturer model/function and schedule comparison",notes))

    # These are explicitly narrow, two-product electrical/control interfaces, not whole-set approvals.
    assertions = [
        ([cm35,cx33], {"interface":"momentary N/O actuator contact to CX-33 dry input","conditions":["Wire the actuator to a selected dry input.","Configure that input as N/O for the chosen CX-33 mode.","Set and verify the intended sequence/mode."]}, "Camden documents the CM-35N/4 as a momentary normally-open contact and the CX-33 dry inputs as programmable for N/O or N/C contacts. This supports this contact interface when wired and programmed accordingly; it does not establish that the selected CX-33 mode produces the required automatic-door sequence."),
        ([cx33,ed100], {"interface":"CX-33 relay contact to ED100 X4 activation input","conditions":["Use a CX-33 relay output as a contact closure only.","Connect to an ED100 X4 activation input per the ED100 instructions.","Select and verify a CX-33 mode/output assignment that requests the intended operator action."]}, "Camden documents Form C relay outputs; dormakaba documents normally-open activation contacts at ED100 X4. This supports a dry-contact activation interface under the listed wiring/configuration conditions only."),
        ([cx33,product_ids["9540"]], {"interface":"RCI 9540 contact to CX-33 dry input","conditions":["Wire COM and the appropriate NO or NC lead to a CX-33 dry input.","Configure the input polarity for the selected CX-33 mode.","Verify the door-closed contact state at commissioning."]}, "The RCI 9540 provides SPDT open/closed loop contacts; its installation sheet identifies COM, N/C and N/O leads and indicates the contact state with the door closed. Camden documents programmable N/O or N/C CX-33 inputs. This supports a selectable contact interface only."),
        ([cx33,product_ids["915"]], {"interface":"RCI 915 relay contact to CX-33 dry input","conditions":["Provide the RCI 915's separately specified 12/24 VDC supply.","Wire a Form C relay contact to a CX-33 dry input.","Configure input polarity and CX-33 mode for the intended egress/access-control behavior."]}, "The RCI 915 provides two Form C relay outputs; Camden documents CX-33 dry inputs programmable for N/O or N/C. This supports a relay-contact interface only and does not establish the access-control sequence or complete egress design."),
    ]
    for product_pair, conditions, rationale in assertions:
        pair = sorted(product_pair)
        db.execute("INSERT OR IGNORE INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?,'compatible',?,?,?,?, 'manufacturer_document')", (json.dumps(pair,separators=(",",":")),json.dumps(conditions,separators=(",",":")),rationale,"Camden and dormakaba manufacturer interface comparison — Belleville Set 2",sources["report"][1]))

    # Save the RCI contact's terminal pinout as evidence and keep the missing power/fit questions visible.
    contact = product_ids["9540"]
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'installation_requirement',?,?)", (contact,source_ids["rci9540_manual"],"Wiring diagram and door-closed contact note","Green = COM, red = N/C, white = N/O; contact state shown with door closed. Drill 3/4-inch diameter x 1-inch deep."))
    db.execute("INSERT OR IGNORE INTO product_evidence(product_id,evidence_source_id,relation,locator,excerpt) VALUES (?,?,'installation_requirement',?,?)", (206,source_ids["mlr"],"Electrical input and wiring requirements","QED100 MLR requires filtered and regulated 24 VDC ±10%, 1 A maximum inrush and 400 mA maximum holding current; direct supply wiring is specified without relays or access-control units between supply and module."))
    warning = ("Set 2 / door 100B is not confirmed as a complete assembly. The schedule names a generic localized power supply but gives no model or output rating. The QED111-MLR instructions require the matching specified 24 VDC supply; confirm the supply, current capacity and wiring. The schedule's 1310-8 mullion is a DORMA removable-mullion family member, but manufacturer material specifically identifies QRM100 as pre-prepped for QED100; do not assume the standard 1310 is prepared for QED100 without checking the 1310 template. The card reader model R5M1-XT0111C0B0NN/SC has not been verified against a primary manufacturer specification. Door 100B is shown as a pair, 965 mm per leaf and 45 mm thick; confirm exit-device sizing/preparation, pair leaf allocation, operator configuration, handing, header/reveal, and electrical design before approval.")
    db.execute("INSERT OR IGNORE INTO research_notes(topic,related_components,guidance,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,'research_lead')", ("Belleville Set 2: whole-assembly unresolved requirements",json.dumps(["1310-8 mullion","QED111","QED111-MLR","ED100","CX-33","RCI 9540","RCI 915","R5M1-XT0111C0B0NN/SC","localized power supply"]),warning,sources["report"][0],sources["report"][1]))

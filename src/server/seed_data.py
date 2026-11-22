"""Seed manufacturer-backed products and compatibility evidence."""
import json

from .catalog import (
    MANUFACTURER_PRODUCT_FACTS, NORTON_5800_VARIANTS, NORTON_5800_ACCESSORIES,
    NORTON_6000_VARIANTS, RECORD_8100_CONFIGURATIONS, OPERATOR_GUIDE_URL,
)

def seed_manufacturer_product_data(db):
    """One-time conversion of blog-only leads to cited manufacturer data."""
    for (manufacturer, model), fact in MANUFACTURER_PRODUCT_FACTS.items():
        row = db.execute("SELECT id FROM products WHERE category='automatic_operator' AND manufacturer=? AND model=? AND source_url=? AND evidence_status='research_lead'", (manufacturer, model, OPERATOR_GUIDE_URL)).fetchone()
        if row:
            db.execute(
                "UPDATE products SET name=?,specifications=?,source_title=?,source_url=?,evidence_status='manufacturer_document',notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (fact["name"], json.dumps(fact["specifications"]), fact["source_title"], fact["source_url"], fact["notes"], row["id"]),
            )

    # Add newly verified ED100 interfaces to existing manufacturer-sourced
    # records without replacing other specification fields or user edits.
    ed100_fact = MANUFACTURER_PRODUCT_FACTS[("dormakaba", "ED100")]
    ed100 = db.execute("SELECT id,specifications,source_url FROM products WHERE category='automatic_operator' AND manufacturer='dormakaba' AND model='ED100' AND source_title=?", (ed100_fact["source_title"],)).fetchone()
    if ed100:
        specifications = json.loads(ed100["specifications"] or "{}")
        changed = False
        for key in ("line_power", "activation_inputs", "accessory_power_output", "locking_device_interface"):
            if key not in specifications:
                specifications[key] = ed100_fact["specifications"][key]
                changed = True
        local_source = ed100["source_url"].startswith("https://my.dormakaba.com/medias/")
        if changed or local_source:
            db.execute("UPDATE products SET specifications=?,source_url=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (json.dumps(specifications), ed100_fact["source_url"] if local_source else ed100["source_url"], ed100["id"]))

    norton_source = MANUFACTURER_PRODUCT_FACTS[("Norton Rixson", "5800 ADAEZ Pro")]
    norton_base_specs = norton_source["specifications"]
    for model, name, side, hardwire_kit in NORTON_5800_VARIANTS:
        specs = {**norton_base_specs, "record_scope": "exact_model", "model_number": model, "mounting_side": side, "hardwire_transformer_kit_included": hardwire_kit}
        specs["opening_limits"] = {**norton_base_specs["opening_limits"], "requires_additional_fit_review": True}
        specs["5800_supported_activation_interfaces"] = (["wired_pushbutton", "wireless_rf_pushbutton", "wave_to_open", "touchless_wall_switch", "wireless_remote"] if model == "5845" else ["wired_pushbutton", "wireless_rf_pushbutton", "touchless_wall_switch"])
        db.execute(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            ("automatic_operator", "Norton Rixson", model, name, json.dumps(specs), norton_source["source_title"], norton_source["source_url"], "manufacturer_document", "Exact 5800-series variant; confirm arm, wall-switch option and installation instructions for the ordered configuration."),
        )

    for model, name, interface, wireless in NORTON_5800_ACCESSORIES:
        specs = {"record_scope": "exact_model", "activation_interface": interface, "wireless": wireless, "manufacturer_series": "5800 Series ADAEZ"}
        db.execute(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            ("activation_device", "Norton Rixson", model, name, json.dumps(specs), norton_source["source_title"], norton_source["source_url"], "manufacturer_document", "Listed as a related 5800-series accessory; verify exact controls/receiver and wiring in the current operator manual."),
        )

    six_thousand_source = MANUFACTURER_PRODUCT_FACTS[("Norton Rixson", "6000 Series")]
    for model, name, side, arm, max_angle in NORTON_6000_VARIANTS:
        specs = {**six_thousand_source["specifications"], "record_scope": "exact_model", "model_number": model, "mounting_side": side, "arm_configuration": arm, "opening_limits": {"min_width_in": 36, "max_width_in": 48, "requires_additional_fit_review": True}}
        if max_angle:
            specs["max_opening_angle_deg"] = max_angle
        db.execute(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            ("automatic_operator", "Norton Rixson", model, name, json.dumps(specs), six_thousand_source["source_title"], six_thousand_source["source_url"], "manufacturer_document", "Exact model number and side/arm type taken from the manufacturer model list. Check its exact template for opening dimensions and handing."),
        )

    record_source = MANUFACTURER_PRODUCT_FACTS[("Record", "8100")]
    for model, name, handing, swing_direction, arm in RECORD_8100_CONFIGURATIONS:
        specs = {**record_source["specifications"], "record_scope": "exact_configuration", "model_configuration": model, "handing": handing, "swing_direction": swing_direction, "arm_configuration": arm, "opening_limits": {"max_width_in": 48, "configurations": ["single"], "handings": [handing], "swing_directions": [swing_direction], "requires_additional_fit_review": True}}
        db.execute(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            ("automatic_operator", "Record", model, name, json.dumps(specs), record_source["source_title"], record_source["source_url"], "manufacturer_document", "Configuration naming follows the manufacturer's 8100 drawings; verify door prep, arm and specific selected controls from the corresponding drawing."),
        )

    # Camden's restroom kit manuals document exact controller, switch, strike,
    # emergency-call and annunciator combinations. These approvals are scoped
    # to the published kit/wiring configuration only.
    camden_products = [
        ("controller", "CX-33", "CX-33 Multi-Function Relay", {
            "record_scope": "exact_model", "input_count": 5, "dry_input_count": 4,
            "wet_input_count": 1, "relay_outputs": 3,
            "relay_contact_type": "Form C SPDT", "relay_output_type": "dry_contact",
            "relay_current_a": 3, "relay_voltage_vdc": 24,
            "supply_options": ["12VAC", "24VAC", "12VDC", "24VDC"],
        }, "CX-33 Multi-Function Relay product page", "https://www.camdencontrols.com/category/control/Relais_multifonctions/products/CX_33", "Manufacturer specifications; relay ratings and mode wiring must be checked for the chosen application."),
        ("activation_device", "CM-8536VR", "CM-8536VR touchless column switch", {
            "record_scope": "exact_model", "activation_interface": "touchless_column_switch",
            "supply_options": ["12VDC", "24VDC"], "peak_current_ma": 45,
            "output_contact_type": "dry_contact", "contact_rating_a": 1,
            "contact_rating_vdc": 30,
        }, "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)", "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1", "Exact switch model listed as a CX-WC17SLVR kit component; use the manual's specific wiring and mode setup."),
        ("activation_device", "CM-221", "CM-221 built-in hands-free switch", {
            "record_scope": "exact_model", "activation_interface": "hands_free_infrared",
            "adjustable_range_in": [2, 8], "adjustable_delay_seconds": [0.5, 20],
            "included_in_kit": "CX-WC17SLVR",
        }, "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)", "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1", "The current kit manual states this hands-free switch is built into the CX-WC17SLVR kit; review its separate instructions for setup."),
        ("washroom_control", "CX-WC17SLVR", "CX-WC17SLVR Restroom Control Kit", {
            "record_scope": "exact_kit", "included_models": ["CX-33", "CM-8536VR x3", "CM-221"],
            "included_components": ["surface mounting contact", "occupied/locked signs"],
            "documented_modes": [7, 8], "controller_model": "CX-33",
            "switch_model": "CM-8536VR",
        }, "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)", "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1", "Use the exact included components and the documented mode/wiring diagram; field operator and locking hardware must be selected separately."),
        ("washroom_control", "CX-WC16-PS-M1", "CX-WC16-PS-M1 Restroom Control Kit with Power Supply", {
            "record_scope": "exact_kit", "controller_model": "60-40E035",
            "supply_input_options": ["12VAC", "24VAC", "12VDC", "24VDC"],
            "included_power_output": {
                "voltage": "24VAC", "max_current_a": 2,
                "source_model": "60-40E035",
                "documented_models": ["CX-ED1799L-8", "CX-WEC10-K2", "CM-AF141SO", "CM-AF540SO"],
            },
            "documented_accessories": ["CM-331/42WS-SGLR", "CM-325/42WS", "CM-331/43S-SGLR", "CX-WEC10-K2", "CX-ED1799L-8", "CM-AF141SO", "CM-AF540SO"],
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "Manual documents the kit's controller and specific field-device wiring; confirm exact supply and wiring from the diagrams."),
        ("controller", "60-40E035", "60-40E035 Advanced Logic Control Relay with 2A Power Supply", {
            "record_scope": "exact_model", "relay_outputs": 3,
            "relay_contact_type": "Form C SPDT", "relay_output_type": "dry_contact",
            "supply_model": "CX-TRX-5024", "supply_output": "24VAC, 50VA",
            "integrated_power_supply_current_a": 2,
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "The WC16 kit manual identifies model 60-40E035 as its prewired logic relay and 2A power supply; check the exact diagram for loads and wiring."),
        ("emergency_call", "CX-WEC10-K2", "CX-WEC10-K2 Emergency Call System", {
            "record_scope": "exact_model", "system_type": "restroom_emergency_call",
            "documented_with": ["CX-WC16-PS-M1", "CM-AF141SO", "CM-AF540SO"],
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "This exact emergency-call system is shown in the manual's restroom kit wiring diagram."),
        ("alarm", "CM-AF141SO", "CM-AF141SO Audio/Visual Annunciator", {
            "record_scope": "exact_model", "alarm_interface": "restroom_call_annunciator",
            "supply_voltage": "24VDC", "documented_with": ["CX-WEC10-K2", "CX-WC16-PS-M1"],
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "Shown as part of the documented CX-WEC10-K2 restroom call wiring; check CM-AF141SO manual for its own ratings."),
        ("alarm", "CM-AF540SO", "CM-AF540SO Audio/Visual Annunciator", {
            "record_scope": "exact_model", "alarm_interface": "restroom_call_annunciator",
            "supply_voltage": "24VDC", "documented_with": ["CX-WEC10-K2", "CX-WC16-PS-M1"],
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "Shown as part of the documented CX-WEC10-K2 restroom call wiring; verify exact device ratings and wiring."),
        ("electric_strike", "CX-ED1799L-8", "CX-ED1799L-8 Electric Strike", {
            "record_scope": "exact_model", "supply_options": ["12VAC", "24VAC", "12VDC", "24VDC"],
            "dc_current_ma_at_12v": 300, "dc_current_ma_at_24v": 150,
            "fail_modes": ["fail_safe", "fail_secure"], "fire_rating_hours": 3,
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "The exact strike is specified in the manual; select voltage/fail mode and confirm frame, latch, listing and load requirements."),
        ("door_contact", "CX-MDA", "CX-MDA Surface Magnetic Door Contact", {
            "record_scope": "exact_model", "contact_type": "magnetic", "output_contact_type": "dry_contact",
        }, "Camden Restroom Control Kits", "https://www.camdencontrols.com/products/WC_Restroom_Control_Kits/kits", "Listed by Camden as a surface magnetic door contact for restroom-control applications; verify the selected kit, contact and circuit details."),
        ("activation_device", "CM-331/42WS-SGLR", "CM-331/42WS-SGLR Wave-to-Open Switch", {
            "record_scope": "exact_model", "activation_interface": "wave_to_open",
            "documented_role": "outside wave-to-open", "output_contact_type": "dry_contact",
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "Exact model is shown in the published kit wiring diagram; match the manual's wiring and selected mode."),
        ("activation_device", "CM-325/42WS", "CM-325/42WS Wave-to-Open Switch", {
            "record_scope": "exact_model", "activation_interface": "wave_to_open",
            "documented_role": "inside wave-to-open", "output_contact_type": "dry_contact",
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "Exact model is shown in the published kit wiring diagram; match the manual's wiring and selected mode."),
        ("activation_device", "CM-331/43S-SGLR", "CM-331/43S-SGLR Wave-to-Lock Switch", {
            "record_scope": "exact_model", "activation_interface": "wave_to_lock",
            "documented_role": "wave-to-lock", "output_contact_type": "dry_contact",
        }, "CX-WC16-PS-M1 Restroom Control Manual", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf", "Exact model is shown in the published kit wiring diagram; match the manual's wiring and selected mode."),
    ]
    for category, model, name, specs, source_title, source_url, notes in camden_products:
        db.execute(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (category, "Camden Controls", model, name, json.dumps(specs), source_title, source_url, "manufacturer_document", notes),
        )

    camden_power_products = [
        (
            "CX-PS13",
            "CX-PS13 V3 Variable Output Linear Power Supply",
            {
                "record_scope": "exact_model",
                "power_requirements": {
                    "accepted_voltages": ["24VAC"],
                    "documented_source_models": ["CX-TRX-4024"],
                },
                "input_voltage": "24VAC",
                "power_output": {
                    "voltage": "24VDC",
                    "max_current_a": 0.8,
                    "documented_models": ["CX-33", "CM-8536VR"],
                },
                "selectable_output_voltages": ["12VDC", "24VDC"],
                "output_current_a": 0.8,
                "requires_transformer": "CX-TRX-4024",
            },
            "CX-PS13 V3 Installation Instructions",
            "https://www.camdencontrols.com/pipelines/resource/7935_CX_PS13V3_Manual_R1.pdf",
            "Camden's CX-WC17SLVR instructions recommend the regulated CX-PS13 for the strike and CX-33. This modeled setup uses its 24VDC output; the CX-PS13 requires a matching AC transformer.",
        ),
        (
            "CX-TRX-4024",
            "CX-TRX-4024 40VA 24VAC Transformer",
            {
                "record_scope": "exact_model",
                "mains_input_voltage": "120VAC",
                "power_output": {
                    "voltage": "24VAC",
                    "output_va": 40,
                    "max_current_a": round(40 / 24, 3),
                    "documented_models": ["CX-PS13"],
                },
                "output_voltage": "24VAC",
                "output_va": 40,
            },
            "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)",
            "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=8",
            "Camden lists the CX-TRX-4024 as a required 40VA, 24VAC transformer for the CX-WC17SLVR and CX-WEC10K2 equipment package; it is the documented AC input source for the CX-PS13.",
        ),
    ]
    for model, name, specs, source_title, source_url, notes in camden_power_products:
        db.execute(
            "INSERT INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES ('power_supply','Camden Controls',?,?,?,?,?,'manufacturer_document',?) ON CONFLICT(category,manufacturer,model) DO UPDATE SET name=excluded.name,specifications=excluded.specifications,source_title=excluded.source_title,source_url=excluded.source_url,evidence_status='manufacturer_document',notes=excluded.notes,updated_at=CURRENT_TIMESTAMP",
            (model, name, json.dumps(specs), source_title, source_url, notes),
        )

    # Exact Dormakaba models found in the Belleville schedule's electrified sets.
    dormakaba_schedule_products = [
        (
            "exit_device", "626QED111-MLR", "Dormakaba QED111 rim exit device with MLR, 626 satin chrome",
            {
                "record_scope": "exact_configuration", "manufacturer_family": "QED 100 Series",
                "device_type": "rim_exit_device", "function": "rim_hex_dog", "finish": "626 satin chrome",
                "electrification": "MLR motorized latch retraction", "power_input": {
                    "voltage": "24VDC +/- 10%", "max_inrush_a": 1, "max_holding_current_a": 0.4,
                    "supply_type": "filtered_and_regulated", "polarity": "non_polarized",
                },
                "conductors": {"power_wires": 2, "optional_feedback_wires": 2},
                "wire_run_by_gauge_ft": {"22AWG": 70, "20AWG": 110, "18AWG": 180, "16AWG": 280, "14AWG": 450, "12AWG": 720},
                "standards": ["ANSI/BHMA A156.3 Grade 1"],
                "opening_limits": {"nominal_device_length_in": 48, "field_sizable_min_door_width_in": 36, "standard_door_thickness_in": 1.75, "min_rim_stile_width_in": 4.25},
                "fire_rating_note": "QED111 is the hex-dog function; the schedule does not identify the QED113 fire-rated function. Verify the exact door/device listing before use on a rated opening.",
            },
            "Dormakaba QED 100 Series Installation Instructions and Specifications",
            "/evidence/dormakaba/QED100_MLR_Installation_Instructions.pdf",
            "The Belleville schedule lists 626QED111-MLR at 1219 mm. Manufacturer data specifies the QED 100 MLR power, wire-run limits, sizing, and prep. The linked file is the exact MLR instruction sheet; do not infer a fire-rated configuration from QED111.",
        ),
        (
            "hinge", "628661HD-CE-12EA", "Dormakaba 661HD concealed electric hinge, CE-12, 12-wire Easy Access",
            {
                "record_scope": "exact_configuration", "canonical_model": "661HD CE-12",
                "hinge_type": "full_mortise_aluminum_geared_continuous", "power_transfer_type": "concealed_electric_hinge",
                "conductor_count": 12, "conductor_gauge_awg": 22, "handing": "non_handed_standard_size",
                "nominal_door_height_in": 84, "actual_hinge_length_in": 83,
                "wire_transfer_note": "CE hinges conduct current through the hinge to electric locks, exit devices, or hold-open devices regardless of door position.",
                "opening_limits": {"door_thickness_in": 1.75, "supports_180_degree_opening": True},
            },
            "Dormakaba 661HD CE-12 12-Wire Easy Access Hinge Template",
            "/evidence/dormakaba/661HD_CE12_Hinge_Template.pdf",
            "The schedule's 2108 mm dimension matches the manufacturer's standard 83 in hinge length. The schedule's RHR label is retained as source text; the standard 661HD CE-12 template describes the hinge as non-handed. Verify the exact catalog suffix, handing requirement if cut, conductor assignment and electrical load.",
        ),
    ]
    for category, model, name, specs, source_title, source_url, notes in dormakaba_schedule_products:
        db.execute(
            "INSERT INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(category,manufacturer,model) DO UPDATE SET name=excluded.name,specifications=excluded.specifications,source_title=excluded.source_title,source_url=excluded.source_url,evidence_status='manufacturer_document',notes=excluded.notes,updated_at=CURRENT_TIMESTAMP",
            (category, "dormakaba", model, name, json.dumps(specs), source_title, source_url, "manufacturer_document", notes),
        )

    qed = db.execute("SELECT id FROM products WHERE category='exit_device' AND manufacturer='dormakaba' AND model='626QED111-MLR'").fetchone()
    electric_hinge = db.execute("SELECT id FROM products WHERE category='hinge' AND manufacturer='dormakaba' AND model='628661HD-CE-12EA'").fetchone()
    if qed and electric_hinge:
        product_ids = json.dumps(sorted([qed["id"], electric_hinge["id"]]), separators=(",", ":"))
        db.execute(
            "INSERT OR IGNORE INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?,'compatible','{}',?,?,?,'manufacturer_document')",
            (
                product_ids,
                "The QED 100 MLR instructions route the exit-device conductors through a power transfer device. Dormakaba identifies CE electric hinges as power-transfer components for exit devices, and the scheduled 661HD CE-12 provides 12 conductors. This supports the exact hinge-to-exit-device wiring interface only: use filtered, regulated 24VDC, keep the 22 AWG run within the QED limit (70 ft maximum), and verify the assigned conductors, load, door preparation, and applicable listing.",
                "Dormakaba QED 100 MLR Instructions and 661HD CE-12 Hinge Template",
                "/evidence/dormakaba/QED100_MLR_Installation_Instructions.pdf",
            ),
        )

    # Keep corrected source-scoped seed facts in sync on repeat initialization.
    for category, model, note in [
        ("washroom_control", "CX-WC17SLVR", "The kit manual lists its included surface contact but does not identify the exact contact model. Field operator and locking hardware must be selected separately."),
        ("washroom_control", "CX-WC16-PS-M1", "The kit manual identifies its 60-40E035 controller/power supply and documents the listed lock and annunciator models. Confirm the exact supply configuration and load budget from the wiring diagrams."),
        ("door_contact", "CX-MDA", "Listed by Camden as a surface magnetic door contact for restroom-control applications; verify the selected kit, contact and circuit details."),
    ]:
        specs = next((specs for entry_category, entry_model, _, specs, *_ in camden_products if entry_category == category and entry_model == model), None)
        if specs:
            db.execute("UPDATE products SET specifications=?,notes=?,updated_at=CURRENT_TIMESTAMP WHERE category=? AND manufacturer='Camden Controls' AND model=?", (json.dumps(specs), note, category, model))

    # Starter catalog records for the non-operator groups. These make the
    # selectors usable while keeping broad/series records explicitly scoped;
    # no compatibility is inferred from products merely sharing a catalog.
    starter_catalog = [
        ("door", "Steelcraft", "L18 Series", "Steelcraft L18 18-gauge hollow-metal door series", {
            "record_scope": "series_reference", "construction": "hollow_metal",
            "steel_thickness_gauge": 18, "application": ["interior_heavy_duty", "exterior_heavy_duty"],
            "core_options": ["honeycomb", "polystyrene", "polyurethane"], "nominal_thickness_in": 1.75,
            "opening_limits": {"door_materials": ["metal"], "supports_fire_rated": True, "requires_exact_fire_listing_review": True},
        }, "Steelcraft Technical Data Manual — L Series", "https://us.allegion.com/content/dam/allegion-us-2/web-documents-2/Manual/Steelcraft_Tech_Data_Manual_105001.pdf", "Series reference, not a complete door order. Confirm size, core, edge, rating, hardware preparations and listing on the approved door schedule."),
        ("frame", "Steelcraft", "DW16 Series", "Steelcraft DW16 drywall frame series, 16 gauge", {
            "record_scope": "series_reference", "construction": "hollow_metal_drywall_frame",
            "steel_thickness_gauge": 16, "wall_type": "drywall_partitions",
            "installation": "knock_down", "fire_listing": "application_and_listing_dependent",
            "opening_limits": {"frame_materials": ["steel"], "supports_fire_rated": True, "requires_exact_fire_listing_review": True},
        }, "Steelcraft Technical Data Manual — DW Series", "https://us.allegion.com/content/dam/allegion-us-2/web-files/steelcraft/technical-documents/Steelcraft_Tech_Data_Manual_105001.pdf", "Series reference. Confirm jamb depth, profile, anchors, opening size, hardware preparations and fire listing from the approved frame schedule."),
        ("hinge", "Hager", "BB1279", "Hager BB1279 full-mortise ball-bearing hinge", {
            "record_scope": "exact_configuration", "hinge_type": "full_mortise_unequal_leaf_bottom",
            "bearing_type": "ball_bearing", "material": "steel", "knuckles": 5,
            "nominal_size_in": {"leaf_height": 5, "leaf_width": 4.5},
            "non_removable_pin": True, "handing_required": True,
            "fire_door_use": "verify size, prep and listing for assembly",
        }, "Hager BB1279 Unequal Leaf Bottom Hinge", "https://www.hagerco.com/commercial-hinges/specialty-hinge/bb1279-unequal-leaf-bottom", "Specific unequal-leaf-bottom configuration. Hager requires handing; this variant is intended for heavy/high-frequency openings and 4.5- or 5-inch cut-outs. Confirm actual handing, preparation and size."),
        ("closer", "LCN", "4040XP", "LCN 4040XP heavy-duty surface-mounted closer", {
            "record_scope": "exact_model", "closer_type": "surface_mounted_hydraulic",
            "handing": "non_handed", "spring_power_adjustment": "sizes_1_to_6",
            "mounting_options": ["hinge_pull_side", "push_side_top_jamb", "push_side_parallel_arm"],
            "standards": ["ANSI/BHMA A156.4 Grade 1"], "max_interior_door_width_ft": 5,
            "max_exterior_door_width_ft": 4,
            "opening_limits": {"max_width_by_location_in": {"interior": 60, "exterior": 48}, "requires_additional_fit_review": True},
        }, "LCN 4040XP Series Closers", "https://www.lcnclosers.com/en/products/surface-mounted/4040xp-series-closers.html", "Confirm arm, mount, spring power, door size/weight and fire-door requirements for the exact opening."),
        ("mechanical_lock", "Schlage", "ND80PD", "Schlage ND80PD storeroom cylindrical lock, Sparta lever", {
            "record_scope": "exact_model", "lock_type": "cylindrical_mechanical",
            "function": "storeroom", "lever_design": "Sparta", "handing": "non_handed",
            "manufacturer_family": "ND Series", "fire_rating": "verify exact listing and door assembly",
        }, "Allegion FastTrack Price Book 16 — ND80 Keyed Storeroom", "https://us.allegion.com/content/dam/allegion-us-2/web-files/allegion/price-book/Allegion_FastTrack_Price_Book_110064.pdf", "Function and Sparta lever model identified; select cylinder, finish, latch, strike and door thickness/preparation from the current order guide."),
        ("electric_lock", "Schlage", "ND80EU", "Schlage ND80EU electrically unlocked storeroom lock", {
            "record_scope": "exact_model", "lock_type": "electrified_cylindrical",
            "function": "storeroom", "electrical_mode": "electrically_unlocked",
            "power_loss_state": "outside_lever_locked", "fail_mode": "fail_secure",
            "voltage_options": ["12VDC", "24VDC"], "peak_current_a": 0.24,
            "request_to_exit_option": True,
        }, "Schlage ND Series Electrified Cylindrical Lock Data Sheet", "https://us.allegion.com/content/dam/allegion-us-2/web-files/schlage/information-documents/Schlage_ND_Series_Electrified_Data_Sheet_104999.pdf", "Exact electrical function and nominal electrical data are documented; confirm voltage, REX option, power budget and installation requirements."),
        ("exit_device", "Von Duprin", "99EO-3FT", "Von Duprin 99 rim exit device, exit-only, 3-foot", {
            "record_scope": "exact_configuration", "device_type": "rim_exit_device",
            "function": "exit_only", "nominal_length_ft": 3,
            "door_width_range_in": [28, 36], "handing": "non_handed_except_selected_options",
            "standards": ["ANSI/BHMA A156.3 Grade 1"], "latch_throw_in": 0.75,
            "opening_limits": {"min_width_in": 28, "max_width_in": 36, "requires_additional_fit_review": True},
        }, "Von Duprin 98/99 Series Catalog", "https://us.allegion.com/content/dam/allegion-us-2/web-documents-2/Catalog/Von_Duprin_98.99_Series_Catalog_106590.pdf", "Model configuration is based on the 99 rim-device family, exit-only function and 3-foot size; verify door type, strike/mullion, fire label, trim and options."),
        ("threshold", "Pemko", "2005", "Pemko 2005 latching panic saddle threshold", {
            "record_scope": "exact_model", "threshold_type": "latching_panic_saddle",
            "nominal_width_in": 5, "door_clearance_in": 0.375,
        }, "Pemko 2005 Series Product Page", "https://www.pemko.com/en/products/astragals-meeting-stiles/adjustable-astragals/product-details.aehpdp-2005-series-ag_pemko_87879", "Check the exact opening, sill, door bottom, clearance and applicable accessibility/fire requirements."),
        ("door_seal", "Pemko", "S88", "Pemko S88 adhesive D-profile gasketing", {
            "record_scope": "exact_model", "seal_type": "adhesive_gasket",
            "profile": "D", "standard": "ANSI/BHMA A156.22",
        }, "Pemko S88 Series Product Page", "https://www.pemko.com/en/products/gasketing/adhesive-gaskets/product-details-nm.aehpdp-s88-series-ag_pemko_12012", "Select the correct gasket material/profile and verify clearances, substrate and environmental exposure."),
    ]
    for category, manufacturer, model, name, specs, source_title, source_url, notes in starter_catalog:
        db.execute(
            "INSERT OR IGNORE INTO products(category,manufacturer,model,name,specifications,source_title,source_url,evidence_status,notes) VALUES (?,?,?,?,?,?,?,?,?)",
            (category, manufacturer, model, name, json.dumps(specs), source_title, source_url, "manufacturer_document", notes),
        )
    # One-time migration: earlier starter records predate selected opening
    # constraints. Preserve subsequent user edits.
    for category, model in [("door", "L18 Series"), ("frame", "DW16 Series"), ("closer", "4040XP"), ("exit_device", "99EO-3FT")]:
        seeded = next((entry for entry in starter_catalog if entry[0] == category and entry[2] == model), None)
        if seeded:
            db.execute("UPDATE products SET specifications=? WHERE category=? AND manufacturer=? AND model=? AND json_extract(specifications,'$.opening_limits') IS NULL", (json.dumps(seeded[4]), category, seeded[1], model))

    camden_assertions = [
        (["washroom_control", "CX-WC17SLVR", "controller", "CX-33"], "CX-WC17SLVR includes the CX-33 controller as a documented kit component."),
        (["washroom_control", "CX-WC17SLVR", "activation_device", "CM-8536VR"], "CX-WC17SLVR includes three CM-8536VR touchless column switches."),
        (["washroom_control", "CX-WC17SLVR", "activation_device", "CM-221"], "The current CX-WC17SLVR manual states the kit includes the built-in CM-221 hands-free switch."),
        (["washroom_control", "CX-WC16-PS-M1", "controller", "60-40E035"], "The manual identifies model 60-40E035 as the CX-WC16-PS-M1 prewired logic relay and power supply."),
        (["washroom_control", "CX-WC16-PS-M1", "electric_strike", "CX-ED1799L-8"], "The manual documents this exact strike in the CX-WC16-PS-M1 kit wiring/configuration."),
        (["washroom_control", "CX-WC16-PS-M1", "activation_device", "CM-331/42WS-SGLR"], "The manual documents this exact outside wave-to-open switch in the kit wiring."),
        (["washroom_control", "CX-WC16-PS-M1", "activation_device", "CM-325/42WS"], "The manual documents this exact inside wave-to-open switch in the kit wiring."),
        (["washroom_control", "CX-WC16-PS-M1", "activation_device", "CM-331/43S-SGLR"], "The manual documents this exact wave-to-lock switch in the kit wiring."),
        (["washroom_control", "CX-WC16-PS-M1", "emergency_call", "CX-WEC10-K2"], "The manual shows this emergency-call system wired with the CX-WC16-PS-M1."),
        (["emergency_call", "CX-WEC10-K2", "alarm", "CM-AF141SO"], "The manual shows the CM-AF141SO annunciator in the CX-WEC10-K2 wiring."),
        (["emergency_call", "CX-WEC10-K2", "alarm", "CM-AF540SO"], "The manual shows the CM-AF540SO annunciator in the CX-WEC10-K2 wiring."),
    ]
    for (category_a, model_a, category_b, model_b), rationale in camden_assertions:
        left = db.execute("SELECT id FROM products WHERE category=? AND manufacturer='Camden Controls' AND model=?", (category_a, model_a)).fetchone()
        right = db.execute("SELECT id FROM products WHERE category=? AND manufacturer='Camden Controls' AND model=?", (category_b, model_b)).fetchone()
        if not left or not right:
            continue
        product_ids = json.dumps(sorted([left["id"], right["id"]]), separators=(",", ":"))
        uses_wc16_manual = "CX-WC16-PS-M1" in {model_a, model_b} or "CX-WEC10-K2" in {model_a, model_b}
        source_title = "Camden restroom kit manuals" if uses_wc16_manual else "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)"
        source_url = "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf" if uses_wc16_manual else "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1"
        db.execute(
            "INSERT OR IGNORE INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?, 'compatible', '{}', ?, ?, ?, 'manufacturer_document')",
            (product_ids, rationale, source_title, source_url),
        )

    # Whole-kit and integrated-system assertions are stored as product tuples,
    # not expanded into a claim that every possible pair proves the assembly.
    camden_assembly_tuples = [
        (
            [
                ("washroom_control", "CX-WC17SLVR"),
                ("controller", "CX-33"),
                ("activation_device", "CM-8536VR"),
                ("activation_device", "CM-221"),
            ],
            "The CX-WC17SLVR manual documents this tuple as one kit: CX-33 logic relay, three CM-8536VR column switches, and built-in CM-221 hands-free switch. The model list stores CM-8536VR once; the documented quantity is three. Follow the selected mode and wiring diagram; this does not establish fit with an unlisted door, operator, or lock.",
            "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)",
            "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1",
        ),
        (
            [
                ("washroom_control", "CX-WC17SLVR"),
                ("controller", "CX-33"),
                ("activation_device", "CM-8536VR"),
                ("activation_device", "CM-221"),
                ("power_supply", "CX-PS13"),
                ("power_supply", "CX-TRX-4024"),
            ],
            "The CX-WC17SLVR manual documents the four-device restroom-control kit and identifies the CX-PS13 and CX-TRX-4024 as the additional required power components. This six-model tuple covers the documented control-and-power package; follow its wiring and selected operating mode. It does not establish fit with an unlisted door, strike, or operator.",
            "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)",
            "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=8",
        ),
        (
            [
                ("washroom_control", "CX-WC16-PS-M1"),
                ("controller", "CX-33"),
                ("activation_device", "CM-331/42WS-SGLR"),
                ("activation_device", "CM-325/42WS"),
                ("activation_device", "CM-331/43S-SGLR"),
                ("electric_strike", "CX-ED1799L-8"),
            ],
            "The CX-WC16-PS-M1 manual documents the CX-33-controlled restroom kit with the listed outside wave-to-open, inside wave-to-open, wave-to-lock switches, and CX-ED1799L-8 strike as one configured system. Confirm the selected mode, fail mode, exact wiring, and opening fit.",
            "Camden CX-WC16-PS-M1 Series Restroom Kit Installation Instructions",
            "https://frca.camdencontrols.com/pipelines/resource/129319_WC16_PS_M1_Restroom_Control_Manual.pdf",
        ),
        (
            [
                ("washroom_control", "CX-WC16-PS-M1"),
                ("controller", "60-40E035"),
                ("activation_device", "CM-331/42WS-SGLR"),
                ("activation_device", "CM-325/42WS"),
                ("activation_device", "CM-331/43S-SGLR"),
                ("electric_strike", "CX-ED1799L-8"),
                ("emergency_call", "CX-WEC10-K2"),
                ("alarm", "CM-AF141SO"),
                ("alarm", "CM-AF540SO"),
            ],
            "Camden's CX-WC16-PS-M1 wiring diagram documents this integrated restroom-control and emergency-call configuration, including the listed relay/power module, switches, strike, CX-WEC10-K2, and both annunciators. Apply the diagram's mode, output, and wiring requirements; this tuple does not establish compatibility with additional unlisted hardware.",
            "Camden CX-WC16-PS-M1 Series Restroom Kit Installation Instructions — Emergency Call Integration",
            "https://www.camdencontrols.com/pipelines/resource/a8015_WC16_PS_M1_Restroom_Control_Manual.pdf",
        ),
    ]
    for models, rationale, source_title, source_url in camden_assembly_tuples:
        product_ids = []
        for category, model in models:
            row = db.execute(
                "SELECT id FROM products WHERE category=? AND manufacturer='Camden Controls' AND model=?",
                (category, model),
            ).fetchone()
            if row:
                product_ids.append(row["id"])
        product_ids = sorted(set(product_ids))
        if len(product_ids) != len(models) or len(product_ids) < 3:
            continue
        db.execute(
            "INSERT OR IGNORE INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?,'compatible','{}',?,?,?,'manufacturer_document')",
            (json.dumps(product_ids, separators=(",", ":")), rationale, source_title, source_url),
        )
        if source_url != "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1" and "WC16-PS-M1" in source_title:
            db.execute(
                "UPDATE compatibility_assertions SET source_url=? WHERE product_ids=? AND conditions='{}' AND source_url=?",
                (source_url, json.dumps(product_ids, separators=(",", ":")),
                 "https://www.camdencontrols.com/pipelines/resource/a2505_WC16_PS_M1_Restroom_Control_Manual.pdf"),
            )

    rule_seeds = [
        ("Norton 5800 documented activation interfaces", "automatic_operator", "activation_device", "5800_supported_activation_interfaces", "contains", "activation_interface", norton_source["source_title"], norton_source["source_url"], "The Norton 5800 manufacturer page lists the activation interface. This is interface-level evidence only; confirm exact options, receiver and wiring."),
        ("LCN 9500 Series dry-contact activation input", "automatic_operator", "activation_device", "lcn_activation_input_type", "equals", "output_contact_type", MANUFACTURER_PRODUCT_FACTS[("LCN", "9540")]["specifications"]["supporting_document"]["title"], MANUFACTURER_PRODUCT_FACTS[("LCN", "9540")]["specifications"]["supporting_document"]["url"], "Matching dry normally-open contacts document the input interface only; verify control-box voltage, timing, safety setup and installation instructions."),
        ("Record 8100 electric-strike interface", "automatic_operator", "electric_strike", "8100_integrated_interfaces", "contains", "hardware_interface", record_source["source_title"], record_source["source_url"], "Record documents a built-in electric-strike interface. Confirm strike voltage/current, control wiring, power budget and exact 8100 configuration."),
        ("Record 8100 presence-sensor interface", "automatic_operator", "safety_sensor", "8100_integrated_interfaces", "contains", "hardware_interface", record_source["source_title"], record_source["source_url"], "Record documents a built-in presence-sensor interface. Confirm the exact sensor model, wiring, test signals and safety configuration."),
    ]
    for name, category_a, category_b, spec_a, comparison, spec_b, source_title, source_url, rationale in rule_seeds:
        if not db.execute("SELECT id FROM compatibility_rules WHERE name=?", (name,)).fetchone():
            db.execute(
                "INSERT INTO compatibility_rules(name,category_a,category_b,spec_a,comparison,spec_b,pass_outcome,fail_outcome,rationale,source_title,source_url,evidence_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (name, category_a, category_b, spec_a, comparison, spec_b, "conditional", "conditional", rationale, source_title, source_url, "manufacturer_document"),
            )
    for manufacturer, model in [("Norton Rixson", "6000 Series"), ("Norton Rixson", "5800 ADAEZ Pro"), ("Record", "8100")]:
        db.execute("UPDATE products SET active=0,updated_at=CURRENT_TIMESTAMP WHERE category='automatic_operator' AND manufacturer=? AND model=?", (manufacturer, model))

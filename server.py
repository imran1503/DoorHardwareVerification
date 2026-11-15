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
    "emergency_call": "Emergency assistance call system",
    "door_contact": "Door position / magnetic contact",
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
    ("controller", "emergency_call"),
    ("controller", "door_contact"),
    ("controller", "alarm"),
    ("controller", "washroom_control"),
    ("washroom_control", "activation_device"),
    ("washroom_control", "emergency_release"),
    ("washroom_control", "alarm"),
    ("washroom_control", "power_supply"),
    ("washroom_control", "controller"),
    ("washroom_control", "request_to_exit"),
    ("washroom_control", "door_contact"),
    ("washroom_control", "emergency_call"),
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
    ("emergency_call", "washroom_control"),
    ("emergency_call", "alarm"),
    ("emergency_call", "controller"),
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
    ("Record", "8100", "Record 8100", {"operator_class": "programmable_low_energy", "standard_claim": "ANSI/BHMA A156.19 in low-energy mode"}),
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

MANUFACTURER_PRODUCT_FACTS = {
    ("LCN", "9540"): {
        "name": "LCN 9540 Senior Swing",
        "source_title": "LCN Senior Swing Product Brochure 116501",
        "source_url": "https://us.allegion.com/content/dam/allegion-us-2/web-files/lcn/information-documents/LCN_Senior_Swing_Product_Brochure_116501.pdf",
        "notes": "Manufacturer brochure establishes the 9540 as a surface-mounted, single-door push-side Senior Swing low-energy operator. Door range is 33–48 in and stated capacity is up to 600 lb on doors up to 48 in. The related 9500 Series control-box manual documents dry-contact inputs and relay/accessory outputs; verify the exact control-box voltage and configuration.",
        "specifications": {
            "record_scope": "exact_model",
            "operator_class": "low_energy",
            "standards": ["ANSI/BHMA A156.19"],
            "mounting": "surface_mount",
            "mounting_side": "push",
            "handing": "handed",
            "door_configurations": ["single"],
            "opening_limits": {"min_width_in": 33, "max_width_in": 48, "max_weight_lb": 600, "configurations": ["single"]},
            "lcn_activation_input_type": "dry_NO_contact",
            "safety_input_type": "dry_NO_contact",
            "lock_output": {"type": "Form C dry relay", "max_current_a": 8, "max_voltage_vdc": 30},
            "accessory_power_output": {"voltage": "24 VAC", "max_current_a": 1.5},
            "supporting_document": {"title": "LCN 9500 Series 240V Senior Control Box Installation Instructions 107499", "url": "https://us.allegion.com/content/dam/allegion-us-2/web-documents-2/InstallInstructions/LCN_2800_Series_and_9500_Series_240V_Senior_Control_Box_IS_107499.pdf"},
        },
    },
    ("Norton Rixson", "6000 Series"): {
        "name": "Norton Rixson 6000 Series (family reference)",
        "source_title": "Norton Rixson 6000 Series Low Energy Operator",
        "source_url": "https://www.nortonrixson.com/en/products/low-energy-door-operators/low-energy-operators/product-details.aehpdp-6000-series-aeh_norton_12237",
        "notes": "Series-level product data; select the exact operator number and arm/configuration before making an opening decision. Manufacturer lists 36–48 in door widths, non-handed push/pull mounting, wall switch/hands-free/RF activation, and 1.3 A onboard power. Exact door/arm templates vary by 6011/6021/6031/6051/6061/6071 configuration.",
        "specifications": {
            "record_scope": "series_reference",
            "operator_class": "low_energy",
            "standards": ["ANSI/BHMA A156.19"],
            "mounting_sides": ["push", "pull"],
            "handing": "non_handed",
            "door_width_per_leaf_in": {"min": 36, "max": 48},
            "supported_activation_interfaces": ["wall_switch", "hands_free", "radio_frequency"],
            "onboard_power_current_a": 1.3,
            "traffic_rating": "extra_high_traffic",
            "manufacturer_models": ["6011", "6021", "6031", "6051", "6061", "6071"],
        },
    },
    ("Norton Rixson", "5800 ADAEZ Pro"): {
        "name": "Norton Rixson 5800 ADAEZ Pro (family reference)",
        "source_title": "Norton Rixson 5800 Series Low Energy Operator",
        "source_url": "https://www.nortonrixson.com/en/products/low-energy-door-operators/low-energy-operators/product-details.aehpdp-5800-series-aeh_norton_12234",
        "notes": "Series-level product data; exact model numbers 5811/5813/5831/5833/5845 have different mounting and kit options. Manufacturer lists up to 48 in, 250 lb, push/pull variants, regenerative power or optional 24 VDC transformer, and UL 10C 90-minute certification. Fire-door use still depends on exact door/operator configuration.",
        "specifications": {
            "record_scope": "series_reference",
            "operator_class": "low_energy",
            "standards": ["ANSI/BHMA A156.19"],
            "mounting_sides": ["push", "pull"],
            "handing": "non_handed",
            "opening_limits": {"max_width_in": 48, "max_weight_lb": 250},
            "power_options": ["regenerative_battery", "24VDC_transformer_kit"],
            "supported_activation_interfaces": ["wired_pushbutton", "wireless_rf_pushbutton", "wave_to_open", "touchless_wall_switch", "wireless_remote"],
            "supported_device_interfaces": ["electric_lock", "fire_panel", "access_control"],
            "certification_note": "UL 10C fire-rated to 90 minutes; verify compatibility with the complete listed door assembly and selected options.",
            "manufacturer_models": ["5811", "5813", "5831", "5833", "5845"],
        },
    },
    ("dormakaba", "ED100"): {
        "name": "dormakaba ED100",
        "source_title": "ED100/ED250 Technical Data and Mounting Instructions",
        "source_url": "https://my.dormakaba.com/medias/059799-241011-ED-100-ED-250-moun-instr-en.pdf?context=bWFzdGVyfHJvb3R8ODAxMzcyOHxhcHBsaWNhdGlvbi9wZGZ8aDExL2g4My85MjMwNzY1Njg2ODE0LnBkZnw3OTdkNGE3MDhiY2ExZmI5OGJkYWVjYzQzYjFkMzY2ZmFlNmEzOWRiZjE2M2I0YzExNWZjNjFhNTVkYjBkYjVm",
        "notes": "Manufacturer data: 700–1100 mm door leaf width; up to 160 kg depending on width and lintel/reveal depth. A combined width/weight chart and arm/configuration review are required; independent maxima are not a pass. Available in low- or full-energy configuration. Fire/smoke door use is configuration and listing dependent.",
        "specifications": {
            "record_scope": "model",
            "operator_modes": ["low_energy", "full_energy"],
            "standards": ["ANSI/BHMA A156.19 (low-energy setup)"],
            "mounting_sides": ["push", "pull"],
            "door_configurations": ["single", "pair"],
            "opening_limits": {"min_width_in": 27.56, "max_width_in": 43.31, "max_weight_lb": 352.74, "max_reveal_depth_mm": 300, "requires_combined_width_weight_chart": True},
            "max_power_w": 120,
            "power_details": "See exact regional voltage/version plate and installation documentation.",
            "arm_options": ["push_arm", "deep_push_arm", "pull_arm_with_track", "CPD_pull_arm_with_track", "application_specific_CPD_push_arm_with_track"],
            "fire_door_note": "Some arm configurations are excluded from smoke/fire doors; approval depends on the exact operator, arm, door and listing.",
        },
    },
    ("dormakaba", "ED250"): {
        "name": "dormakaba ED250",
        "source_title": "ED100/ED250 Technical Data and Mounting Instructions",
        "source_url": "https://my.dormakaba.com/medias/059799-241011-ED-100-ED-250-moun-instr-en.pdf?context=bWFzdGVyfHJvb3R8ODAxMzcyOHxhcHBsaWNhdGlvbi9wZGZ8aDExL2g4My85MjMwNzY1Njg2ODE0LnBkZnw3OTdkNGE3MDhiY2ExZmI5OGJkYWVjYzQzYjFkMzY2ZmFlNmEzOWRiZjE2M2I0YzExNWZjNjFhNTVkYjBkYjVm",
        "notes": "Manufacturer data: 700–1600 mm door leaf width; up to 400 kg at reveal depth up to 300 mm depending on width, and a 160 kg maximum for 301–500 mm reveal depth. A combined width/weight chart and arm/configuration review are required; independent maxima are not a pass. Available in low- or full-energy configuration. Fire/smoke door use is configuration and listing dependent.",
        "specifications": {
            "record_scope": "model",
            "operator_modes": ["low_energy", "full_energy"],
            "standards": ["ANSI/BHMA A156.19 (low-energy setup)"],
            "mounting_sides": ["push", "pull"],
            "door_configurations": ["single", "pair"],
            "opening_limits": {"min_width_in": 27.56, "max_width_in": 62.99, "max_weight_lb": 881.85, "max_reveal_depth_mm": 500, "max_weight_lb_above_300mm_reveal": 352.74, "requires_combined_width_weight_chart": True},
            "max_power_w": 240,
            "power_details": "See exact regional voltage/version plate and installation documentation.",
            "arm_options": ["push_arm", "deep_push_arm", "pull_arm_with_track", "CPD_pull_arm_with_track", "application_specific_CPD_push_arm_with_track"],
            "fire_door_note": "Some arm configurations are excluded from smoke/fire doors; approval depends on the exact operator, arm, door and listing.",
        },
    },
    ("Record", "8100"): {
        "name": "Record 8100 (family reference)",
        "source_title": "Record 8100 Swing Door Operator Product Page",
        "source_url": "https://www.recorddoors.com/us/en/products/swing-doors/8100",
        "notes": "Series-level data. Record describes the 8100 as programmable for low-energy use under ANSI 156.19; exact operator/arm/handing configuration is selected from the 8100 drawings. Its sell sheet lists 120 VAC, 15 A supply requirements and 24 VAC, 0.5 A accessory power for maglocks/electric strikes; verify the specific control and load wiring.",
        "specifications": {
            "record_scope": "series_reference",
            "operator_modes": ["high_traffic_automatic", "programmable_low_energy"],
            "low_energy_standard": "ANSI/BHMA A156.19",
            "motor": "24 V, 1/4 hp",
            "line_power": {"voltage": "120 VAC", "current_a": 15, "frequency_hz": 60},
            "accessory_power_output": {"voltage": "24 VAC", "max_current_a": 0.5, "documented_load_types": ["maglock", "electric_strike"]},
            "door_width_by_configuration_in": {"single": 48, "pair": 96},
            "handing": "non_handed operator; order-specific handing/arm configuration",
            "mounting_sides": ["push", "pull"],
            "8100_integrated_interfaces": ["electric_strike", "presence_sensor"],
            "manufacturer_models": ["8101", "8102", "8121", "8122", "8152", "8153", "8154", "8161", "8162", "8164"],
        },
    },
}

NORTON_5800_VARIANTS = [
    ("5811", "Norton Rixson 5811 ADAEZ Pro, pull-side", "pull", False),
    ("5813", "Norton Rixson 5813 ADAEZ Pro, pull-side with hardwire kit", "pull", True),
    ("5831", "Norton Rixson 5831 ADAEZ Pro, push-side", "push", False),
    ("5833", "Norton Rixson 5833 ADAEZ Pro, push-side with hardwire kit", "push", True),
    ("5845", "Norton Rixson 5845 ADAEZ Pro, push or pull", "push_or_pull", True),
]
NORTON_5800_ACCESSORIES = [
    ("ADA1012-1", "Norton Rixson 1-3/4 in push button, no RF transmitter", "wired_pushbutton", False),
    ("ADA1012-2", "Norton Rixson 1-3/4 in push button with RF transmitter", "wireless_rf_pushbutton", True),
    ("ADA1019-1", "Norton Rixson square push button, no RF transmitter", "wired_pushbutton", False),
    ("ADA1019-2", "Norton Rixson square push button with RF transmitter", "wireless_rf_pushbutton", True),
    ("ADA1019-3", "Norton Rixson square DPDT push button, no RF transmitter", "wired_pushbutton", False),
    ("ADA1019-4", "Norton Rixson square DPDT push button with RF transmitter", "wireless_rf_pushbutton", True),
    ("673", "Norton Rixson 673 microwave wave-to-open switch, single", "wave_to_open", False),
    ("674", "Norton Rixson 674 microwave wave-to-open switch, double", "wave_to_open", False),
    ("700", "Norton Rixson 700 wave-to-open switch", "wave_to_open", False),
    ("704", "Norton Rixson 704 narrow touchless wall switch", "touchless_wall_switch", False),
    ("767", "Norton Rixson 767 battery-operated wave-to-open switch, single", "wireless_remote", True),
    ("768", "Norton Rixson 768 battery-operated wave-to-open switch, double", "wireless_remote", True),
]

NORTON_6000_VARIANTS = [
    ("6011", "Norton Rixson 6011, pull side", "pull", "rigid_arm_slide_track", None),
    ("6021", "Norton Rixson 6021, push side, up to 110 degrees", "push", "double_lever_arm", 110),
    ("6031", "Norton Rixson 6031, push side, 110–180 degrees", "push", "double_lever_arm", 180),
    ("6051", "Norton Rixson 6051, pull side", "pull", "pull_side_arm", None),
    ("6061", "Norton Rixson 6061 Unitrol, push side", "push", "unitrol", None),
    ("6071", "Norton Rixson 6071 Unitrol, push side", "push", "unitrol", None),
]
RECORD_8100_CONFIGURATIONS = [
    ("8101-LH-inswing-standard", "Record 8101 LH inswing, standard arm", "left", "inswing", "standard_arm"),
    ("8121-RH-inswing-standard", "Record 8121 RH inswing, standard arm", "right", "inswing", "standard_arm"),
    ("8102-LH-inswing-track", "Record 8102 LH inswing, track arm", "left", "inswing", "track_arm"),
    ("8122-RH-inswing-track", "Record 8122 RH inswing, track arm", "right", "inswing", "track_arm"),
    ("8101-LHR-outswing-standard", "Record 8101 LHR outswing, standard arm", "left_reverse", "outswing", "standard_arm"),
    ("8121-RHR-outswing-standard", "Record 8121 RHR outswing, standard arm", "right_reverse", "outswing", "standard_arm"),
    ("8102-LHR-outswing-track", "Record 8102 LHR outswing, track arm", "left_reverse", "outswing", "track_arm"),
    ("8122-RHR-outswing-track", "Record 8122 RHR outswing, track arm", "right_reverse", "outswing", "track_arm"),
]

def seed_manufacturer_product_data(db):
    """One-time conversion of blog-only leads to cited manufacturer data."""
    for (manufacturer, model), fact in MANUFACTURER_PRODUCT_FACTS.items():
        row = db.execute("SELECT id FROM products WHERE category='automatic_operator' AND manufacturer=? AND model=? AND source_url=? AND evidence_status='research_lead'", (manufacturer, model, OPERATOR_GUIDE_URL)).fetchone()
        if row:
            db.execute(
                "UPDATE products SET name=?,specifications=?,source_title=?,source_url=?,evidence_status='manufacturer_document',notes=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (fact["name"], json.dumps(fact["specifications"]), fact["source_title"], fact["source_url"], fact["notes"], row["id"]),
            )

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
        }, "CX-WC17SLVR Restroom Control Kit Manual", "https://www.camdencontrols.com/pipelines/resource/11374_WC17SLVR_Restroom_Control_Manual_R2.pdf", "Exact switch model listed as a CX-WC17SLVR kit component; use the manual's specific wiring and mode setup."),
        ("activation_device", "CM-221", "CM-221 built-in hands-free switch", {
            "record_scope": "exact_model", "activation_interface": "hands_free_infrared",
            "adjustable_range_in": [2, 8], "adjustable_delay_seconds": [0.5, 20],
            "included_in_kit": "CX-WC17SLVR",
        }, "CX-WC17SLVR Restroom Control Kit Manual", "https://www.camdencontrols.com/pipelines/resource/11374_WC17SLVR_Restroom_Control_Manual_R2.pdf", "The current kit manual states this hands-free switch is built into the CX-WC17SLVR kit; review its separate instructions for setup."),
        ("washroom_control", "CX-WC17SLVR", "CX-WC17SLVR Restroom Control Kit", {
            "record_scope": "exact_kit", "included_models": ["CX-33", "CM-8536VR x3", "CM-221"],
            "included_components": ["surface mounting contact", "occupied/locked signs"],
            "documented_modes": [7, 8], "controller_model": "CX-33",
            "switch_model": "CM-8536VR",
        }, "CX-WC17SLVR Restroom Control Kit Manual", "https://www.camdencontrols.com/pipelines/resource/11374_WC17SLVR_Restroom_Control_Manual_R2.pdf", "Use the exact included components and the documented mode/wiring diagram; field operator and locking hardware must be selected separately."),
        ("washroom_control", "CX-WC16-PS-M1", "CX-WC16-PS-M1 Restroom Control Kit with Power Supply", {
            "record_scope": "exact_kit", "controller_model": "60-40E035",
            "supply_input_options": ["12VAC", "24VAC", "12VDC", "24VDC"],
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
    # Keep corrected source-scoped seed facts in sync on repeat initialization.
    for category, model, note in [
        ("washroom_control", "CX-WC17SLVR", "The kit manual lists its included surface contact but does not identify the exact contact model. Field operator and locking hardware must be selected separately."),
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
        db.execute(
            "INSERT OR IGNORE INTO compatibility_assertions(product_ids,outcome,conditions,rationale,source_title,source_url,evidence_status) VALUES (?, 'compatible', '{}', ?, ?, ?, 'manufacturer_document')",
            (product_ids, rationale, "Camden restroom kit manuals", "https://www.camdencontrols.com/pipelines/resource/1007_WC16_PS_M1_Restroom_Control_Manual.pdf" if "CX-WC16-PS-M1" in {model_a, model_b} or "CX-WEC10-K2" in {model_a, model_b} else "https://www.camdencontrols.com/pipelines/resource/11374_WC17SLVR_Restroom_Control_Manual_R2.pdf"),
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
        seed_manufacturer_product_data(db)
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

def spec_value(product, path):
    value = product["specifications"]
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value

def pair_evaluation(db, product_a, product_b, context=None):
    # A compatibility record cannot be stronger than the product records it
    # relies on. Keep the pair visible, but do not present its result as verified
    # until both exact models have sourced specifications.
    if not trusted_product_record(product_a) or not trusted_product_record(product_b):
        broad_records = [product for product in (product_a, product_b) if product["specifications"].get("record_scope") in {"series_reference", "model_family"}]
        if broad_records:
            broad = ", ".join(product["name"] for product in broad_records)
            return {"status": "unverified", "rationale": f"{broad} is a product-series reference, not the exact scheduled model. Its size, hardware preparations, reinforcement and fire listing are needed before this pair can be assessed."}
        return {"status": "unverified", "rationale": "One or both products still need exact manufacturer-backed model specifications before this pair can be assessed."}
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
        left = spec_value(left_product, rule["spec_a"])
        right = spec_value(right_product, rule["spec_b"])
        passed = compare_specs(left, rule["comparison"], right)
        if passed is None:
            outcomes.append({"status": "unverified", "rationale": f"Cannot evaluate {rule['name']}: a required specification is missing or not comparable.", "source_title": rule["source_title"], "source_url": rule["source_url"], "evidence_status": rule["evidence_status"]})
        elif not trusted_evidence(rule["evidence_status"]):
            outcomes.append({"status": "unverified", "rationale": f"Rule '{rule['name']}' still needs verified evidence.", "source_title": rule["source_title"], "source_url": rule["source_url"], "evidence_status": rule["evidence_status"]})
        else:
            outcomes.append({"status": rule["pass_outcome"] if passed else rule["fail_outcome"], "rationale": rule["rationale"], "source_title": rule["source_title"], "source_url": rule["source_url"], "evidence_status": rule["evidence_status"], "rule_id": rule["id"]})
    if not outcomes:
        categories = {product_a["category"], product_b["category"]}
        if categories == {"closer", "exit_device"}:
            return {"status": "unverified", "rationale": "A surface closer and rim exit device are commonly specified on the same opening, but that does not prove these exact models fit together. Confirm the closer arm/mount, exit-device template, clearance, door/frame reinforcement and fire-door listing against the final door schedule."}
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
    """Compare supplied opening details with sourced product constraints."""
    if not opening:
        return []
    relevant_categories = {"automatic_operator", "door", "frame", "hinge", "closer", "mechanical_lock", "electric_lock", "electric_strike", "exit_device"}
    findings = []
    discrete_limits = {
        "door_materials": "door_material",
        "frame_materials": "frame_material",
        "configurations": "configuration",
        "handings": "handing",
        "swing_directions": "swing_direction",
        "locations": "location",
    }
    numeric_limits = {
        "max_width_in": ("width_in", "max"),
        "min_width_in": ("width_in", "min"),
        "max_height_in": ("height_in", "max"),
        "min_height_in": ("height_in", "min"),
        "max_weight_lb": ("weight_lb", "max"),
        "min_weight_lb": ("weight_lb", "min"),
        "max_reveal_depth_mm": ("reveal_depth_mm", "max"),
    }
    relevant_context = {
        "door": {"door_material", "configuration", "handing", "swing_direction", "location", "fire_rated", "width_in", "height_in", "weight_lb"},
        "frame": {"frame_material", "configuration", "handing", "swing_direction", "location", "fire_rated", "width_in", "height_in", "reveal_depth_mm"},
        "hinge": {"configuration", "handing", "swing_direction", "fire_rated", "width_in", "height_in", "weight_lb"},
        "closer": {"configuration", "handing", "swing_direction", "location", "fire_rated", "width_in", "height_in", "weight_lb"},
        "automatic_operator": {"configuration", "handing", "swing_direction", "location", "fire_rated", "width_in", "height_in", "weight_lb", "reveal_depth_mm"},
        "mechanical_lock": {"configuration", "handing", "swing_direction", "fire_rated", "width_in", "height_in"},
        "electric_lock": {"configuration", "handing", "swing_direction", "fire_rated", "width_in", "height_in"},
        "electric_strike": {"configuration", "handing", "swing_direction", "fire_rated", "width_in", "height_in"},
        "exit_device": {"configuration", "handing", "swing_direction", "fire_rated", "width_in", "height_in"},
    }
    for product in products:
        if product["category"] not in relevant_categories:
            continue
        relevant_values = relevant_context.get(product["category"], set())
        if not any(opening.get(key) not in (None, "") for key in relevant_values):
            continue
        limits = product["specifications"].get("opening_limits")
        if not trusted_evidence(product["evidence_status"]):
            findings.append({"status": "unverified", "product_a": product, "rationale": f"{product['name']} is a research lead; its opening details cannot be used as a verified product constraint."})
            continue
        limits = limits if isinstance(limits, dict) else {}
        scope = product["specifications"].get("record_scope")
        exact_product = trusted_product_record(product)
        failures, missing = [], []
        checked = []
        validated_context = set()

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
                failures.append(f"selected {context_key.replace('_', ' ')} {value} conflicts with {product['name']} (documented: {', '.join(limits[limit_key])})")
            else:
                checked.append(f"{context_key.replace('_', ' ')} {value} matches the selected product")
                validated_context.add(context_key)
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
            else:
                checked.append(f"{context_key.replace('_', ' ')} {value:g} is within the documented limit")
                validated_context.add(context_key)
        if "max_weight_lb_above_300mm_reveal" in limits:
            reveal, weight = opening.get("reveal_depth_mm"), opening.get("weight_lb")
            if reveal in (None, "") and weight not in (None, ""):
                missing.append("frame reveal depth (mm) for the model's weight limit")
            elif reveal not in (None, "") and weight not in (None, ""):
                try:
                    if 300 < float(reveal) <= 500 and float(weight) > float(limits["max_weight_lb_above_300mm_reveal"]):
                        failures.append(f"door weight {float(weight):g} lb exceeds the documented limit for a reveal over 300 mm")
                except (TypeError, ValueError):
                    missing.append("valid reveal depth and door weight")
        width_by_location = limits.get("max_width_by_location_in")
        if isinstance(width_by_location, dict) and (opening.get("location") not in (None, "") or opening.get("width_in") not in (None, "")):
            location, width = opening.get("location"), opening.get("width_in")
            if location in (None, ""):
                missing.append("opening location for the closer's width limit")
            elif location not in width_by_location:
                missing.append("manufacturer's width limit for this opening location")
            else:
                validated_context.add("location")
                if width in (None, ""):
                    missing.append("door width")
                else:
                    try:
                        if float(width) > float(width_by_location[location]):
                            failures.append(f"door width {float(width):g} in exceeds the {location} limit of {width_by_location[location]:g} in for {product['name']}")
                        else:
                            checked.append(f"door width {float(width):g} in is within the {location} limit")
                        validated_context.add("width_in")
                    except (TypeError, ValueError):
                        missing.append("valid door width")
        if "supports_fire_rated" in limits:
            rated = opening.get("fire_rated")
            if rated in (None, ""):
                missing.append("fire rating")
            elif rated == "yes":
                if not limits["supports_fire_rated"]:
                    failures.append("the model is not documented for a fire-rated opening")
                else:
                    checked.append("fire-rated use is documented for this product line")
                validated_context.add("fire_rated")
            else:
                checked.append("fire rating recorded as not rated")
                validated_context.add("fire_rated")
        if limits.get("requires_exact_fire_listing_review") and opening.get("fire_rated") == "yes":
            missing.append("exact fire-door listing for the selected door/frame configuration")
        if limits.get("requires_combined_width_weight_chart") and opening.get("width_in") not in (None, "") and opening.get("weight_lb") not in (None, ""):
            missing.append("manufacturer's combined width/weight functional chart review")
        if limits.get("requires_additional_fit_review"):
            missing.append("manufacturer's complete installation/fit review")
        for context_key in relevant_context.get(product["category"], set()):
            if opening.get(context_key) not in (None, "") and context_key not in validated_context:
                missing.append(f"manufacturer data to evaluate {context_key.replace('_', ' ')} for this model")
        if failures:
            status, rationale = "incompatible", "; ".join(failures) + "."
        elif not exact_product:
            status = "unverified"
            detail = ("Opening details considered: " + "; ".join(checked) + ". " if checked else "")
            scope_note = "This is a series-level reference; the exact product/configuration is needed."
            pending = " Remaining review: " + ", ".join(sorted(set(missing))) + "." if missing else ""
            if opening.get("width_in") not in (None, "") or opening.get("height_in") not in (None, ""):
                pending += " The selected series record does not provide dimensions for the exact scheduled door/frame."
            rationale = detail + scope_note + pending
        elif missing:
            status, rationale = "unverified", "Opening information is missing for documented limits: " + ", ".join(sorted(set(missing))) + "."
        elif not limits:
            status, rationale = "unverified", f"No sourced opening-fit limits are recorded for {product['name']}."
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
            set_key = json.dumps(product_ids, separators=(",", ":"))
            exact = db.execute("SELECT * FROM compatibility_assertions WHERE product_ids=? ORDER BY updated_at DESC LIMIT 1", (set_key,)).fetchone()
            context = data.get("context", {}) if isinstance(data.get("context", {}), dict) else {}
            context = {**opening, **context}
            findings = []
            exact_applies = False
            if exact:
                assertion = assertion_dict(exact)
                conditions_match = all(context.get(key) == value for key, value in assertion["conditions"].items())
                products_documented = all(trusted_product_record(product) for product in products)
                if trusted_evidence(assertion["evidence_status"]) and conditions_match and products_documented:
                    exact_applies = True
                    findings.append({"status": assertion["outcome"], "rationale": assertion["rationale"], "source_title": assertion["source_title"], "source_url": assertion["source_url"]})
            if not exact_applies:
                for left_index, product_a in enumerate(products):
                    for product_b in products[left_index + 1:]:
                        evaluation = pair_evaluation(db, product_a, product_b, context)
                        findings.append({"product_a": product_a, "product_b": product_b, **evaluation})
            findings.extend(opening_fit_findings(products, opening))
            if len(products) == 1 and not findings:
                findings.append({"status": "unverified", "product_a": products[0], "rationale": "No opening-fit constraint is documented for this selected product category."})
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
            return self.send_json({"status": status, "message": messages[status], "assertion": assertion if exact_applies else None, "products": products, "findings": findings})

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

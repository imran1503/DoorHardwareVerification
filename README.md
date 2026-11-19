# Door Hardware Checker — Pro Security Controls Inc.

A React interface and local SQLite database for recording exact hardware models, their specifications, and evidence-backed compatibility. Missing evidence is shown as **unverified**; product category or similarity alone never implies compatibility.

## Run locally

Requirements: Python 3.10+ and Node.js 18+.

1. Install frontend packages with `npm install`.
2. In one terminal, run `python3 -m src.server` from this folder. This creates `doorhardware.db` in the project root and starts the API at `http://127.0.0.1:8000`.
3. In a second terminal, run `npm run dev` and open the Vite URL (usually `http://localhost:5173`).

Restart the API after backend changes. SQLite is the source of truth; back up `doorhardware.db` to preserve catalog and evidence records.

Backend code lives in `src/server/`: `__main__.py` starts the app, `api.py` defines HTTP routes, `database.py` manages SQLite, `catalog.py` holds labels and reference data, `seed_data.py` loads product/evidence records, `catalog_refresh.py` refreshes public catalog listings, `compatibility.py` evaluates product pairs, and `opening_fit.py` checks opening constraints. Run backend tests with `python3 -m unittest discover -s tests -v`.

The product catalog's **Refresh live catalogs** action fetches allowlisted public Camden, ADI, Wesco, and BG Distribution pages. The API also refreshes on startup and every 24 hours while it is running. Imported listings remain `research_lead` records and do not create compatibility assertions. `GET /api/catalog/status` reports the latest run; `POST /api/catalog/refresh` starts an on-demand refresh.

## Maintaining the compatibility library

- **Product catalog:** add each exact make/model once. Put comparable facts in the Specifications JSON object (for example `{"input_voltage":"24V DC","activation_input":"dry_contact"}`). Use consistent keys and values across models so reusable rules can compare them.
- **Opening details:** enter door/frame materials, configuration, handing, location, fire-rating, and dimensions/weight when checking an assembly. A product's Specifications JSON can include sourced `opening_limits`, such as `{"opening_limits":{"max_width_in":48,"max_weight_lb":250,"door_materials":["wood","metal"],"supports_fire_rated":true}}`. The check compares only limits explicitly recorded for that model; missing model limits or missing required opening details remain unverified.
- **Power path:** record load requirements as `power_requirements.accepted_voltages` and `power_requirements.current_a`; record a supply as `power_output.voltage` and `power_output.max_current_a`. ADO `accessory_power_output` can also be evaluated when its allowed load is documented. If an exact ADO output is missing, early screening provisionally assumes nominal 24V; AC/DC type, current capacity, and load eligibility remain unverified, and this assumption never counts a dry relay as a power source. The assembly check flags a missing supply as conditional, a documented voltage/current conflict as incompatible, and incomplete ratings as unverified. A 12V-only strike still needs a correctly rated 12V supply or converter.
- **CSV import:** use **Download CSV template** in the catalog, then **Import CSV**. `specifications` must be valid JSON in each CSV cell. A repeated category, manufacturer, and model updates that catalog row.
- **Bulk evidence import:** use **Download template** and **Import JSON** on either Rules & assertions or Compatibility research. One JSON file can contain any mix of reusable rules, exact-product assertions, and research notes. Product references in assertions must match an active catalog product's category, manufacturer, and model exactly. Importing creates new records or updates a matching record; invalid rows are skipped and reported, while valid rows in the same file still import. Coverage is generated from the catalog and interaction categories, so importing assertions fills the matching generated rows rather than loading a separate matrix.
- **Evidence status:** research leads are discovery notes only. Manufacturer documentation, field-verified, and company-approved records need a source URL. The checker uses sourced evidence and shows missing or untrusted facts as unverified.
- **Reusable rules:** use for repeatable interface facts between component categories, such as matching a device output to a controller input. Choose a rule only when the cited source supports the comparison and its pass/fail outcomes.
- **Specific combinations:** use assertions for exact product pairs or a complete multi-device kit, such as a CX-33 washroom setup with push buttons, emergency release, push-to-unlock, and alarm. Include the source, conditions, and rationale. A multi-product assertion does not automatically apply to its subsets.
- **Coverage:** relevant product pairs are generated from declared component interactions; the app does not store an all-to-all X matrix. Add categories to `INTERACTION_PAIRS` in `src/server/catalog.py` when a new component relationship should be tracked. Each applicable pair remains visible until it has a sourced result.
- **Assembly checks:** pairwise passes do not prove that a three-or-more-product system works as a whole. Record an assembly-level assertion or field test for the complete set.

### JSON evidence bundle format

The downloaded template starts with empty arrays. Add records to any section, leaving unused sections empty. This example shows the field structure only; replace the example text, URL, condition, outcome, and evidence status with verified information before importing it:

```json
{
  "compatibilityRules": [
    {
      "name": "Controller activation input matches device output",
      "category_a": "controller",
      "category_b": "activation_device",
      "spec_a": "activation_input",
      "comparison": "equals",
      "spec_b": "output_contact_type",
      "pass_outcome": "conditional",
      "fail_outcome": "conditional",
      "rationale": "Confirm wiring and operating mode in the cited documentation.",
      "source_title": "Manufacturer wiring guide",
      "source_url": "https://example.com/wiring-guide.pdf",
      "evidence_status": "manufacturer_document"
    }
  ],
  "assertions": [
    {
      "products": [
        { "category": "washroom_control", "manufacturer": "Camden Controls", "model": "CX-WC17SLVR" },
        { "category": "controller", "manufacturer": "Camden Controls", "model": "CX-33" }
      ],
      "outcome": "conditional",
      "conditions": { "example_condition": "Replace with a documented requirement" },
      "rationale": "Example only: replace with what the source says about this exact combination.",
      "source_title": "Manufacturer installation instructions",
      "source_url": "https://example.com/instructions.pdf",
      "evidence_status": "research_lead"
    }
  ],
  "researchNotes": [
    {
      "topic": "Washroom kit configuration",
      "related_components": "Washroom controls · activation · emergency release",
      "guidance": "Summarize the lead and what still needs confirmation.",
      "source_title": "Product guide",
      "source_url": "https://example.com/product-guide",
      "evidence_status": "research_lead"
    }
  ]
}
```

Allowed rule comparisons are `equals`, `not_equals`, `less_or_equal`, `greater_or_equal`, and `contains`. Rule categories must use the catalog category keys shown in `PRODUCT_CATEGORIES` in `src/server/catalog.py`. Assertion outcomes are `compatible`, `incompatible`, or `conditional`. Evidence statuses are `research_lead`, `manufacturer_document`, `field_verified`, and `company_approved`; only use a verified status when the source supports that claim. `conditions` must be a JSON object. The example links and condition are placeholders and should be replaced before import.

The ZenSupply operator guide is retained as research leads for operator families and design questions. It is not treated as manufacturer proof or compatibility approval. The database also preserves the earlier lookup tables and sample rules; the new model does not use those legacy examples to approve exact-model assemblies.

## API

The Python API uses only the standard library. `GET /api/bootstrap` returns the catalog, categories, rules, assertions, and research notes. `GET /api/coverage` generates relevant pair coverage. `POST /api/compatibility/check` evaluates a selected assembly. Product, rule, assertion, and CSV import endpoints support the editing screens; the older `/api/check` endpoint remains for compatibility with the original UI.

This local development build has no authentication or access control. Use an authenticated company service and a review process before hosting it for shared production use.

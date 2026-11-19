"""Evidence-backed product-pair compatibility evaluation."""
import json
import re

from .catalog import INTERACTION_PAIRS
from .database import (
    assertion_dict, compatibility_rule_dict, connect, product_dict,
    trusted_evidence, trusted_product_record,
)

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


def _voltage_values(value):
    if isinstance(value, (list, tuple, set)):
        return {token for item in value for token in _voltage_values(item)}
    if not isinstance(value, (str, int, float)):
        return set()
    text = str(value).upper()
    matches = re.findall(r"(?<!\d)(\d+(?:\.\d+)?)\s*V?\s*(VAC|VDC|AC|DC)(?![A-Z])", text)
    return {f"{float(number):g}V{'AC' if kind.endswith('AC') else 'DC'}" for number, kind in matches}


def _voltage_nominals(values):
    return {
        f"{float(match):g}V"
        for value in values
        if (match := re.match(r"(\d+(?:\.\d+)?)V(?:AC|DC)$", value))
    }


def _current_capacity(specs, output=None):
    output = output if isinstance(output, dict) else {}
    for source in (output, specs):
        for key in ("max_current_a", "output_current_a", "current_capacity_a", "available_current_a", "integrated_power_supply_current_a"):
            value = source.get(key)
            if isinstance(value, (int, float)) and value >= 0:
                return float(value)
    return None


def _load_current(specs, voltage, output=None):
    output = output if isinstance(output, dict) else {}
    requirements = specs.get("power_requirements", {})
    if isinstance(requirements, dict):
        for key in ("current_a", "peak_current_a", "max_current_a"):
            value = requirements.get(key)
            if isinstance(value, (int, float)) and value >= 0:
                return float(value)
    for key in ("peak_current_a", "max_current_a", "rated_current_a", "current_draw_a", "current_a"):
        value = specs.get(key)
        if isinstance(value, (int, float)) and value >= 0:
            return float(value)
    voltage_match = re.match(r"(\d+)V(AC|DC)", voltage or "")
    if voltage_match:
        voltage_value, current_type = voltage_match.groups()
        specific = specs.get(f"{current_type.lower()}_current_ma_at_{voltage_value}v")
        if isinstance(specific, (int, float)) and specific >= 0:
            return float(specific) / 1000
    for key in ("peak_current_ma", "current_ma"):
        value = specs.get(key)
        if isinstance(value, (int, float)) and value >= 0:
            return float(value) / 1000
    return None


def _power_sources(products):
    sources = []
    for product in products:
        specs = product["specifications"]
        candidates = []
        if isinstance(specs.get("power_output"), dict):
            candidates.append(specs["power_output"])
        if isinstance(specs.get("included_power_output"), dict):
            candidates.append(specs["included_power_output"])
        if isinstance(specs.get("accessory_power_output"), dict):
            candidates.append(specs["accessory_power_output"])
        # Some seeded controllers document their integrated transformer output
        # as a string plus a separate current rating.
        if specs.get("integrated_power_supply_current_a") and specs.get("supply_output"):
            candidates.append({
                "voltage": specs["supply_output"],
                "max_current_a": specs["integrated_power_supply_current_a"],
                "documented_models": specs.get("documented_powered_models", []),
            })
        if product["category"] == "power_supply" and not candidates:
            candidates.append(specs)
        for index, output in enumerate(candidates):
            voltages = set()
            voltage_keys = ("output_voltage", "output_voltage_options") if output is specs else ("voltage", "output_voltage", "output_voltage_options", "voltage_options")
            for key in voltage_keys:
                voltages.update(_voltage_values(output.get(key)))
            if not voltages:
                continue
            sources.append({
                "product": product,
                "output": output,
                "voltages": voltages,
                "capacity_a": _current_capacity(specs, output),
                "explicit_supply": product["category"] == "power_supply",
                "key": (product["id"], index),
            })
    return sources


def _power_requirements(product):
    specs = product["specifications"]
    requirements = specs.get("power_requirements", {})
    requirements = requirements if isinstance(requirements, dict) else {}
    values = []
    for key in ("accepted_voltages", "voltage_options", "required_voltage", "supply_voltage"):
        values.append(requirements.get(key))
    for key in ("supply_options", "voltage_options", "supply_voltage_options", "supply_voltage", "input_voltage", "operating_voltage"):
        values.append(specs.get(key))
    return {token for value in values for token in _voltage_values(value)}


def power_path_findings(products):
    """Check selected low-voltage loads against explicitly selected outputs.

    Dry relay/contact ratings are intentionally never read as power outputs.
    A missing/mismatched supply is a conditional installation requirement,
    unless a selected power supply itself has a documented incompatible output.
    """
    sources = _power_sources(products)
    findings = []
    assigned = {}
    documented_ado_outputs = {
        source["product"]["id"]
        for source in sources
        if source["product"]["category"] == "automatic_operator"
    }
    assumed_ado_outputs = []
    for product in products:
        specs = product["specifications"]
        has_output_record = any(specs.get(key) for key in ("power_output", "accessory_power_output"))
        if product["category"] == "automatic_operator" and product["id"] not in documented_ado_outputs and not has_output_record:
            assumption = {
                "product": product,
                "nominal_voltages": {"24V"},
                "assumed": True,
                "capacity_a": None,
                "explicit_supply": False,
                "key": (product["id"], "provisional-ado-24v"),
            }
            sources.append(assumption)
            assumed_ado_outputs.append(assumption)
    selected_supply_without_specs = any(
        product["category"] == "power_supply" and not any(source["product"]["id"] == product["id"] for source in sources)
        for product in products
    )
    explicit_supply_has_output = any(source["explicit_supply"] for source in sources)

    for load in products:
        requirements = _power_requirements(load)
        if not requirements:
            continue
        requirement_nominals = _voltage_nominals(requirements)
        matches = [
            source for source in sources
            if not source.get("assumed")
            and source["product"]["id"] != load["id"]
            and requirements & source["voltages"]
        ]
        matches.sort(key=lambda source: (not source["explicit_supply"], source["capacity_a"] is None))
        if not matches:
            if selected_supply_without_specs:
                status = "unverified"
                rationale = f"{load['name']} lists accepted supply voltages, but the selected power supply has no documented output voltage. Record its output before checking the path."
            elif explicit_supply_has_output:
                status = "incompatible"
                rationale = f"No selected power source provides {', '.join(sorted(requirements))} for {load['name']}. The selected supply output conflicts; use a correctly rated supply or converter."
            elif assumed_ado_outputs:
                status = "conditional"
                assumed_names = ", ".join(source["product"]["name"] for source in assumed_ado_outputs)
                if "24V" in requirement_nominals:
                    rationale = f"Provisional assumption: {assumed_names} has nominal 24V accessory power. That matches a 24V option for {load['name']} only; verify AC/DC type, current capacity, selected device voltage and the operator's actual output from its exact manual."
                else:
                    rationale = f"Provisional assumption: {assumed_names} is nominally 24V, which does not directly match {load['name']}'s {', '.join(sorted(requirements))} requirement. Select a matching supply or converter, then verify the exact operator output and wiring."
            else:
                status = "conditional"
                rationale = f"{load['name']} requires one of {', '.join(sorted(requirements))}; no matching supply output is selected. Add a correctly rated power supply. A dry relay can switch a supply but cannot provide or convert its voltage."
            source_product = assumed_ado_outputs[0]["product"] if assumed_ado_outputs else load
            findings.append({"finding_type": "power_path", "status": status, "product_a": load, "product_b": source_product if assumed_ado_outputs else None, "source_title": source_product["source_title"], "source_url": source_product["source_url"], "rationale": rationale})
            continue

        source = matches[0]
        output = source["output"]
        voltage = sorted(requirements & source["voltages"])[0]
        demand_a = _load_current(load["specifications"], voltage)
        capacity_a = source["capacity_a"]
        allowed_models = output.get("documented_models", output.get("documented_load_models", []))
        allowed_types = output.get("documented_load_types", [])
        model_documented = load["model"].lower() in {str(value).lower() for value in allowed_models}
        if source["explicit_supply"] and not (allowed_models or allowed_types):
            scope_documented = True
        else:
            scope_documented = (
                load["model"].lower() in {str(value).lower() for value in allowed_models}
                or load["category"] in {str(value).lower() for value in allowed_types}
            )
        if demand_a is not None and capacity_a is not None:
            assigned.setdefault(source["key"], {"source": source, "loads": []})["loads"].append((load, demand_a))

        if not scope_documented:
            status = "conditional"
            rationale = f"{source['product']['name']} provides {voltage}, but its documentation does not list {load['name']} as an approved load. Confirm the wiring and permitted load."
        elif model_documented and capacity_a is not None and trusted_product_record(source["product"]) and trusted_product_record(load):
            status = "compatible"
            rationale = f"The manufacturer documents {load['name']} with the included {voltage} supply in this product configuration. Confirm the full assembly wiring and combined load budget."
        elif demand_a is None or capacity_a is None:
            status = "conditional"
            rationale = f"{source['product']['name']} matches {load['name']} at {voltage}, but the load current or source capacity is missing, so the power budget cannot be confirmed."
        elif not trusted_product_record(source["product"]) or not trusted_product_record(load):
            status = "unverified"
            rationale = f"The {voltage} power path is a specification match ({demand_a:g} A load, {capacity_a:g} A source), but one or both records still need exact manufacturer-backed specifications."
        else:
            status = "compatible"
            rationale = f"The documented {voltage} output can supply the documented {demand_a:g} A load within its {capacity_a:g} A rating; confirm the exact wiring diagram and total circuit load."
        findings.append({"finding_type": "power_path", "status": status, "product_a": load, "product_b": source["product"], "source_title": source["product"]["source_title"], "source_url": source["product"]["source_url"], "rationale": rationale})

    for assignment in assigned.values():
        source = assignment["source"]
        capacity = source["capacity_a"]
        total = sum(current for _, current in assignment["loads"])
        if total > capacity:
            names = ", ".join(load["name"] for load, _ in assignment["loads"])
            findings.append({
                "finding_type": "power_path", "status": "incompatible",
                "product_a": assignment["loads"][0][0], "product_b": source["product"],
                "source_title": source["product"]["source_title"], "source_url": source["product"]["source_url"],
                "rationale": f"Combined documented load for {names} is {total:g} A, above {source['product']['name']}'s {capacity:g} A output rating.",
            })
    return findings

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

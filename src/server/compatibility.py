"""Evidence-backed product-pair compatibility evaluation."""
import json

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

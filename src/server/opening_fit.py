"""Compare an opening's dimensions and configuration with product limits."""
from .database import trusted_evidence, trusted_product_record

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

"""Run the source-backed compatibility behavior benchmark.

Run from the repository root with:
    python -m src.server.compatibility_benchmark

This evaluates the same Handler.check_assembly path used by the HTTP API. The
cases are acceptance expectations based on stored evidence and evaluator rules;
they are not field-test claims about installed openings.
"""
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from .api import _JsonHarness, Handler
from .database import connect, initialize


WC17_FOUR = [
    "CX-WC17SLVR", "CX-33", "CM-8536VR", "CM-221",
]
WC17_SIX = WC17_FOUR + ["CX-PS13", "CX-TRX-4024"]
WC16_SIX = [
    "CX-WC16-PS-M1", "CX-33", "CM-331/42WS-SGLR", "CM-325/42WS",
    "CM-331/43S-SGLR", "CX-ED1799L-8",
]
WC16_NINE = [
    "CX-WC16-PS-M1", "60-40E035", "CM-331/42WS-SGLR", "CM-325/42WS",
    "CM-331/43S-SGLR", "CX-ED1799L-8", "CX-WEC10-K2", "CM-AF141SO",
    "CM-AF540SO",
]
ABH_CONFLICT_PAIR = ["7414 ARJ", "1013"]
ABH_CHART_CONTEXT = {
    "door_width_in": 36,
    "opening_angle_deg": 90,
    "hinge_type": "butt_hinges",
}


def _resolve_ids(db, models):
    ids = []
    for model in models:
        matches = list(db.execute(
            "SELECT id,manufacturer FROM products WHERE active=1 AND model=? "
            "AND manufacturer IN ('Camden Controls','Architectural Builders Hardware Mfg. Inc.','dormakaba')",
            (model,),
        ))
        if len(matches) != 1:
            raise RuntimeError(f"Expected one active catalog record for {model!r}; found {len(matches)}.")
        ids.append(matches[0]["id"])
    return ids


def _cases(db):
    six_with_extra = WC17_SIX + ["CX-WEC10-K2"]
    return [
        {"name": "Camden WC17 documented four-model kit", "models": WC17_FOUR,
         "expected": "compatible", "source": "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)",
         "url": "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1"},
        {"name": "Camden WC17 documented six-model control and power package", "models": WC17_SIX,
         "expected": "compatible", "source": "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)",
         "url": "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=8"},
        {"name": "Camden WC16 documented six-model restroom kit", "models": WC16_SIX,
         "expected": "compatible", "source": "Camden CX-WC16-PS-M1 Series Restroom Kit Installation Instructions",
         "url": "https://frca.camdencontrols.com/pipelines/resource/129319_WC16_PS_M1_Restroom_Control_Manual.pdf"},
        {"name": "Camden WC16 documented nine-model emergency-call configuration", "models": WC16_NINE,
         "expected": "compatible", "source": "Camden CX-WC16-PS-M1 Series Restroom Kit Installation Instructions — Emergency Call Integration",
         "url": "https://www.camdencontrols.com/pipelines/resource/a8015_WC16_PS_M1_Restroom_Control_Manual.pdf"},
        {"name": "ABH chart conflict under its stated installation assumptions", "models": ABH_CONFLICT_PAIR,
         "context": ABH_CHART_CONTEXT, "expected": "incompatible",
         "source": "ABH Closer and Overhead Holder Compatibility Chart",
         "url": "https://www.abhmfg.com/content/documents/0000107_overhead_holder_compatibility_chart_with_other_manufacturers_closers.pdf"},
        {"name": "Same ABH products without matching installation conditions", "models": ABH_CONFLICT_PAIR,
         "expected": "unverified", "source": "ABH Closer and Overhead Holder Compatibility Chart",
         "url": "https://www.abhmfg.com/content/documents/0000107_overhead_holder_compatibility_chart_with_other_manufacturers_closers.pdf"},
        {"name": "WC17 six-model kit plus an undocumented seventh product", "models": six_with_extra,
         "expected": "unverified", "source": "Camden CX-WC17SLVR Series Restroom Kit Installation Instructions (Rev. Nov 3, 2025)",
         "url": "/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=8"},
    ]


def run_benchmark():
    initialize()
    results = []
    with connect() as db:
        for case in _cases(db):
            product_ids = _resolve_ids(db, case["models"])
            harness = _JsonHarness()
            Handler.check_assembly(harness, {
                "product_ids": product_ids,
                "context": case.get("context", {}),
            })
            response_code, result = harness.response
            actual = result.get("status", "error") if response_code == 200 else "error"
            results.append({
                **case,
                "models": list(case["models"]),
                "actual": actual,
                "passed": actual == case["expected"],
                "subset_checks": result.get("subset_checks", []),
                "response_code": response_code,
            })
    return results


def render_report(results):
    by_size = defaultdict(list)
    subset_evidence = defaultdict(dict)
    for result in results:
        by_size[len(result["models"])].append(result)
        for check in result["subset_checks"]:
            key = (tuple(check["product_ids"]), tuple(sorted(result.get("context", {}).items())))
            subset_evidence[check["subset_size"]][key] = check["status"]

    correct = sum(result["passed"] for result in results)
    unique_subset_count = sum(len(checks) for checks in subset_evidence.values())
    resolved_subset_count = sum(
        status in {"compatible", "incompatible"}
        for checks in subset_evidence.values()
        for status in checks.values()
    )
    lines = [
        "# Compatibility behavior benchmark",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "This is a reproducible behavior benchmark for the evaluator, not field validation or proof that a complete installed opening will work. Positive expectations require an exact manufacturer-documented tuple; conflict expectations apply only to the cited assumptions. The extra-product case checks that evidence for a smaller tuple is not stretched to a larger assembly.",
        "",
        "Run from the repository root with `python -m src.server.compatibility_benchmark`.",
        "",
        "## Results by selected group size",
        "",
        "| Products selected | Cases passed | Cases | Expected verdicts |",
        "| ---: | ---: | ---: | --- |",
    ]
    for size in sorted(by_size):
        group = by_size[size]
        expected = ", ".join(f"{r['name']}: {r['actual']}" for r in group)
        lines.append(f"| {size} | {sum(r['passed'] for r in group)} | {len(group)} | {expected} |")
    lines.extend([
        "",
        f"Overall: **{correct}/{len(results)} acceptance cases passed**.",
        "",
        "## Exact subset evidence coverage",
        "",
        "Subset coverage counts a subset as determined only when an exact assertion returns a compatible or incompatible verdict in that context. Conditional and unverified rows remain unresolved; inferred compatibility is not counted.",
        "",
        "| Subset size | Resolved exact checks | Unique subsets evaluated |",
        "| ---: | ---: | ---: |",
    ])
    for size in sorted(subset_evidence):
        statuses = list(subset_evidence[size].values())
        resolved = sum(status in {"compatible", "incompatible"} for status in statuses)
        lines.append(f"| {size} | {resolved} | {len(statuses)} |")
    lines.extend([
        "",
        f"Across these selected cases, **{resolved_subset_count} of {unique_subset_count} unique subset checks ({resolved_subset_count / unique_subset_count:.1%})** returned a sourced compatible or incompatible outcome. The remainder stayed conditional or unverified, so this benchmark demonstrates correct evidence handling but does not show that unknowns are rare.",
    ])
    lines.extend(["", "## Cases and evidence", ""])
    for result in results:
        mark = "PASS" if result["passed"] else "FAIL"
        lines.append(f"- **{mark} - {result['name']}** ({len(result['models'])} products): expected `{result['expected']}`, got `{result['actual']}`. [Source]({result['url']})")
    lines.extend([
        "",
        "## Limits",
        "",
        "- The sample is deliberately small and biased toward manufacturer-documented Camden kits plus one condition-scoped ABH conflict. It is not a statistical estimate of real-world accuracy.",
        "- This is a current behavior score, not a measured before/after improvement. A before-change benchmark snapshot and a larger independently reviewed set are needed to quantify improvement over the prior implementation.",
        "- A compatible tuple proves only the listed control-system combination and stated scope. It does not prove door fit, code compliance, installation quality, or unlisted accessories.",
        "- The conflict case tests the ABH chart's stated 36-inch, 90-degree, butt-hinge assumptions. It must not be applied to the different 965 mm continuous-hinge Belleville opening without further evidence.",
        "- Unknown extra-product combinations are expected to stay unverified until an exact assertion or sufficient model-specific evidence exists.",
        "",
    ])
    return "\n".join(lines)


def main():
    results = run_benchmark()
    report = render_report(results)
    report_path = Path(__file__).resolve().parents[2] / "public" / "evidence" / "compatibility-benchmark-results.md"
    report_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nReport written to: {report_path}")
    if any(not result["passed"] for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

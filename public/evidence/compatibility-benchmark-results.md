# Compatibility behavior benchmark

Generated: 2026-11-21T19:36:26-05:00

This is a reproducible behavior benchmark for the evaluator, not field validation or proof that a complete installed opening will work. Positive expectations require an exact manufacturer-documented tuple; conflict expectations apply only to the cited assumptions. The extra-product case checks that evidence for a smaller tuple is not stretched to a larger assembly.

Run from the repository root with `python -m src.server.compatibility_benchmark`.

## Results by selected group size

| Products selected | Cases passed | Cases | Expected verdicts |
| ---: | ---: | ---: | --- |
| 2 | 2 | 2 | ABH chart conflict under its stated installation assumptions: incompatible, Same ABH products without matching installation conditions: unverified |
| 4 | 1 | 1 | Camden WC17 documented four-model kit: compatible |
| 6 | 2 | 2 | Camden WC17 documented six-model control and power package: compatible, Camden WC16 documented six-model restroom kit: compatible |
| 7 | 1 | 1 | WC17 six-model kit plus an undocumented seventh product: unverified |
| 9 | 1 | 1 | Camden WC16 documented nine-model emergency-call configuration: compatible |

Overall: **7/7 acceptance cases passed**.

## Exact subset evidence coverage

Subset coverage counts a subset as determined only when an exact assertion returns a compatible or incompatible verdict in that context. Conditional and unverified rows remain unresolved; inferred compatibility is not counted.

| Subset size | Resolved exact checks | Unique subsets evaluated |
| ---: | ---: | ---: |
| 2 | 11 | 62 |
| 3 | 0 | 129 |
| 4 | 1 | 171 |
| 5 | 0 | 152 |
| 6 | 2 | 92 |
| 7 | 0 | 37 |
| 8 | 0 | 9 |
| 9 | 1 | 1 |

Across these selected cases, **15 of 653 unique subset checks (2.3%)** returned a sourced compatible or incompatible outcome. The remainder stayed conditional or unverified, so this benchmark demonstrates correct evidence handling but does not show that unknowns are rare.

## Cases and evidence

- **PASS - Camden WC17 documented four-model kit** (4 products): expected `compatible`, got `compatible`. [Source](/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=1)
- **PASS - Camden WC17 documented six-model control and power package** (6 products): expected `compatible`, got `compatible`. [Source](/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=8)
- **PASS - Camden WC16 documented six-model restroom kit** (6 products): expected `compatible`, got `compatible`. [Source](https://frca.camdencontrols.com/pipelines/resource/129319_WC16_PS_M1_Restroom_Control_Manual.pdf)
- **PASS - Camden WC16 documented nine-model emergency-call configuration** (9 products): expected `compatible`, got `compatible`. [Source](https://www.camdencontrols.com/pipelines/resource/a8015_WC16_PS_M1_Restroom_Control_Manual.pdf)
- **PASS - ABH chart conflict under its stated installation assumptions** (2 products): expected `incompatible`, got `incompatible`. [Source](https://www.abhmfg.com/content/documents/0000107_overhead_holder_compatibility_chart_with_other_manufacturers_closers.pdf)
- **PASS - Same ABH products without matching installation conditions** (2 products): expected `unverified`, got `unverified`. [Source](https://www.abhmfg.com/content/documents/0000107_overhead_holder_compatibility_chart_with_other_manufacturers_closers.pdf)
- **PASS - WC17 six-model kit plus an undocumented seventh product** (7 products): expected `unverified`, got `unverified`. [Source](/evidence/camden/WC17SLVR_Restroom_Control_Manual_R2.pdf#page=8)

## Limits

- The sample is deliberately small and biased toward manufacturer-documented Camden kits plus one condition-scoped ABH conflict. It is not a statistical estimate of real-world accuracy.
- This is a current behavior score, not a measured before/after improvement. A before-change benchmark snapshot and a larger independently reviewed set are needed to quantify improvement over the prior implementation.
- A compatible tuple proves only the listed control-system combination and stated scope. It does not prove door fit, code compliance, installation quality, or unlisted accessories.
- The conflict case tests the ABH chart's stated 36-inch, 90-degree, butt-hinge assumptions. It must not be applied to the different 965 mm continuous-hinge Belleville opening without further evidence.
- Unknown extra-product combinations are expected to stay unverified until an exact assertion or sufficient model-specific evidence exists.

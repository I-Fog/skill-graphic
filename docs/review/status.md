# Review Status

Last updated: 2026-06-21

| Area | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Skill identity | Done | `SKILL.md`, `agents/openai.yaml` | `skill-graphic` is discoverable and has a documented workflow. |
| Surface revolution fixture | MVP demo | `examples/surface-revolution/input.json`, `assets/templates/surface_revolution.html` | Works for the canonical OX case; still template-specific. |
| Integral fixture | MVP demo | `examples/indefinite-integral-tan-sin/input.json`, `assets/templates/indefinite_integral.html` | Graphical meaning comes first: integrand, area, primitive, family. |
| Function graph contract | Improved | `references/functions.md`, `examples/function-graph-cubic/input.json` | Typed feature targets and validator exist; renderer is pending. |
| Function render model | Initial slice | `python/compiler/function_graph.py`, `dist/function-graph-cubic.render.json` | Compiles validated continuous functions into curves, viewport, points, intervals, tangents, and timeline. |
| Schema | Partial | `schemas/simulation.schema.json` | Supports three types; still should be split into `$defs` and `oneOf`. |
| Contract semantics | Improved | `python/validator/contract.py` | Required checks, allowed actions, slider refs, unique ids, and action-compatible targets are validated. |
| Math validators | Improved | `python/validator/*.py` | Positive fixtures pass and negative fixtures fail. More edge cases are needed. |
| Generator | Improved | `scripts/generate_simulation.py` | Always reruns validation and rejects stale, failed, or mismatched external math results. |
| Smoke tests | Improved | `scripts/run_smoke_tests.py` | Includes positive fixtures, recursive expected-math checks, and expected negative failure metadata. |
| Browser validation | Local only | `docs/review/screenshots/*.png` | Screenshots are static evidence; no CI browser run yet. |
| ChatGPT Pro review loop | Improved | `scripts/pro_review_cycle.py`, `docs/review/pro-review-automation.md` | Review rounds include `round.json`, anchored nonce markers, final `END_REVIEW`, prompt/response/backlog hashes, UIA transport for the integrated browser, and clipboard fallback. |

## Current Risk Level

- Architectural risk: medium.
- Math-validation risk: medium.
- Visual-runtime risk: medium-high until `function_graph.html` exists.
- Security/portable parsing risk: medium because SymPy parsing is still based on expression strings.

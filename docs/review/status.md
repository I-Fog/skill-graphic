# Review Status

Last updated: 2026-06-21

| Area | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Skill identity | Done | `SKILL.md`, `agents/openai.yaml` | `skill-graphic` is discoverable and has a documented workflow. |
| Surface revolution fixture | MVP demo | `examples/surface-revolution/input.json`, `assets/templates/surface_revolution.html` | Works for the canonical OX case; still template-specific. |
| Integral fixture | MVP demo | `examples/indefinite-integral-tan-sin/input.json`, `assets/templates/indefinite_integral.html` | Graphical meaning comes first: integrand, area, primitive, family. |
| Function graph contract | Partial | `references/functions.md`, `examples/function-graph-cubic/input.json` | Contract and validator exist; renderer is pending. |
| Schema | Partial | `schemas/simulation.schema.json` | Supports three types; still should be split into `$defs` and `oneOf`. |
| Contract semantics | Improved | `python/validator/contract.py` | Required checks, allowed actions, slider refs, and scene targets are validated. |
| Math validators | Improved | `python/validator/*.py` | Positive fixtures pass and negative fixtures fail. More edge cases are needed. |
| Generator | Improved | `scripts/generate_simulation.py` | Runs or verifies validation and rejects stale `contract_hash`. |
| Smoke tests | Improved | `scripts/run_smoke_tests.py` | Includes positive fixtures, expected-math checks, and negative fixture failures. |
| Browser validation | Local only | `docs/review/screenshots/*.png` | Screenshots are static evidence; no CI browser run yet. |

## Current Risk Level

- Architectural risk: medium.
- Math-validation risk: medium.
- Visual-runtime risk: medium-high until `function_graph.html` exists.
- Security/portable parsing risk: medium because SymPy parsing is still based on expression strings.

# Review Status

Last updated: 2026-06-22

| Area | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Skill identity | Done | `SKILL.md`, `agents/openai.yaml` | `skill-graphic` is discoverable and has a documented workflow. |
| Surface revolution fixture | MVP demo | `examples/surface-revolution/input.json`, `assets/templates/surface_revolution.html` | Works for the canonical OX case; still template-specific. |
| Integral fixture | MVP demo | `examples/indefinite-integral-tan-sin/input.json`, `assets/templates/indefinite_integral.html` | Graphical meaning comes first: integrand, area, primitive, family. |
| Function graph contract | Improved | `references/functions.md`, `examples/function-graph-cubic/input.json` | Typed feature targets and validator exist. |
| Function render model | Initial slice | `python/compiler/function_graph.py`, `dist/function-graph-cubic.render.json` | Compiles validated continuous functions into curves, viewport, points, intervals, tangents, and timeline. |
| Function graph renderer | Initial slice | `assets/templates/function_graph.html`, `dist/function-graph-cubic.html`, `docs/review/screenshots/function-graph-cubic.png`, `docs/review/screenshots/function-graph-cubic-primitive.png` | Renders the validated model as one interactive SVG stage with smooth scrubber, formula overlay, tangent/extrema scenes, derivative/primitive layers, and camera motion. |
| Schema | Partial | `schemas/simulation.schema.json` | Supports three types; still should be split into `$defs` and `oneOf`. |
| Contract semantics | Improved | `python/validator/contract.py` | Required checks, allowed actions, slider refs, unique ids, and action-compatible targets are validated. |
| Math validators | Improved | `python/validator/*.py` | Positive fixtures pass and negative fixtures fail. More edge cases are needed. |
| Generator | Improved | `scripts/generate_simulation.py` | Always reruns validation and rejects stale, failed, or mismatched external math results. |
| Smoke tests | Improved | `scripts/run_smoke_tests.py` | Includes positive fixtures, recursive expected-math checks, expected negative failure metadata, generated function HTML checks, static browser-spec presence checks, and Pro packet contract checks. |
| Browser validation | Versioned local check | `tests/browser/function_graph.spec.ts`, `docs/review/screenshots/*.png` | Function renderer has a Playwright spec for navigation, boundaries, derivative/primitive visibility, reload state, and mobile overlay separation. No CI browser run yet. |
| ChatGPT Pro review loop | Improved | `scripts/pro_review_cycle.py`, `docs/review/pro-review-automation.md` | Review rounds use compact scoped packets by default, preserve full-packet fallback, include `FILES_INCLUDED`, require `SCOPE_REVISADO`, write `packet/manifest.json` plus copied files/diff, preserve `round.json`, anchored nonce markers, final `END_REVIEW`, hashes, UIA transport, clipboard fallback, and copied-response prefix trimming. |
| Global supervision | Improved | `$CODEX_HOME\skills\codex-pro-supervisor`, `codex-supervision.json` | Project-agnostic supervisor skill can package scoped rounds into `.codex-supervision/pro-rounds/`, supports configured scopes, accepts explicit `--root`, requires `SCOPE_REVISADO` and `PACKET_SHA256`, skips directory-discovered binaries, blocks staged changes, and blocks explicitly requested unsafe files before sending. |

## Current Risk Level

- Architectural risk: medium.
- Math-validation risk: medium.
- Visual-runtime risk: medium: `function_graph.html` exists for the cubic fixture, but generic coverage and automated visual regression still need expansion.
- Security/portable parsing risk: medium because SymPy parsing is still based on expression strings.

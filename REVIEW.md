# skill-graphic Review Guide

This repository contains a Codex skill scaffold for exact, interactive educational simulations.

The current branch should be reviewed as a **scaffold MVP**, not as a finished generic simulation engine. It contains two visual demos and one reusable function-graph contract, plus validators and smoke checks that are intended to prevent known false positives.

## What To Review First

1. `SKILL.md` - skill entry point and operating contract.
2. `schemas/simulation.schema.json` - declarative simulation contract.
3. `python/validator/contract.py` - required checks, allowed actions, and target validation.
4. `python/validator/function_graph.py` - reusable function graph validation.
5. `python/compiler/function_graph.py` - first function render-model compiler.
6. `scripts/generate_simulation.py` - validation gate before HTML generation.
7. `scripts/run_smoke_tests.py` - positive and negative smoke coverage.
8. `docs/review/status.md` - current implementation status.
9. `docs/review/known-limitations.md` - known gaps to prioritize.

## Current Scope

Implemented:

- Surface of revolution demo for `y = x sqrt(x/a)`.
- Graphical integral demo for `int tan(x)/(2 sen(x)+6) dx`.
- Reusable `function_graph` contract and validator.
- First `function_graph` render model for continuous Cartesian function fixtures.
- Validation gate with `contract_hash` plus live revalidation before rendering.
- Typed feature targets for function scenes.
- Static negative fixtures with expected failure metadata for known false-green cases.

Not implemented yet:

- Generic `function_graph.html` renderer.
- Browser automation in CI.
- Full schema split with `$defs` and `oneOf`.

## Static Review Evidence

Use these files when you cannot execute tests:

- `docs/review/validation-log.md`
- `docs/review/screenshots/surface-revolution.png`
- `docs/review/screenshots/integral-graphic.png`
- `examples/negative/*/input.json`
- `docs/review/pro-review-automation.md`
- `docs/review/pro-rounds/*/prompt.md`, `response.md`, `backlog.md`, and `round.json` when an external Pro review round exists

## Main Reviewer Question

Does the repo now provide a strong enough validated contract to justify building the generic Cartesian renderer next?

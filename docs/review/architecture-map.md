# Architecture Map

```text
examples/*/input.json
  |
  v
schemas/simulation.schema.json
  |
  v
python/validator/contract.py
  - allowed actions by type
  - required checks by type and scene action
  - slider references
  - unique scene/feature ids
  - action-compatible typed targets
  |
  v
python/validator/validate_math.py
  |
  +--> python/validator/surface_revolution.py
  +--> python/validator/indefinite_integral.py
  +--> python/validator/function_graph.py
  |
  v
dist/*.math.json
  - includes passed checks
  - includes contract_hash
  |
  +--> python/compiler/function_graph.py
       - compiles validated function contracts into render models
       - samples curves, points, intervals, tangents, viewport, and timeline
       |
       v
       dist/*function-graph*.render.json
  |
  v
scripts/generate_simulation.py
  - validates schema
  - reruns math validation
  - treats external math result as untrusted cache metadata
  - rejects stale contract_hash
  |
  v
dist/*.html
```

## Main Files

- Skill entry: `SKILL.md`
- Local instructions: `AGENTS.md`
- Schema: `schemas/simulation.schema.json`
- Contract semantics: `python/validator/contract.py`
- Function render-model compiler: `python/compiler/function_graph.py`
- Generator: `scripts/generate_simulation.py`
- Smoke runner: `scripts/run_smoke_tests.py`

## Positive Fixtures

- `examples/surface-revolution/input.json`
- `examples/indefinite-integral-tan-sin/input.json`
- `examples/function-graph-cubic/input.json`

## Negative Fixtures

- `examples/negative/surface-inverted-domain/input.json`
- `examples/negative/function-false-extremum/input.json`
- `examples/negative/function-false-inflection/input.json`
- `examples/negative/function-omitted-asymptote/input.json`
- `examples/negative/function-tangent-missing-point/input.json`
- `examples/negative/function-extrema-target-wrong-kind/input.json`
- `examples/negative/function-duplicate-feature-id/input.json`
- `examples/negative/function-asymptote-missing-target/input.json`

## Visual Evidence

- `docs/review/screenshots/surface-revolution.png`
- `docs/review/screenshots/integral-graphic.png`

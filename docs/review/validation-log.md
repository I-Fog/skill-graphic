# Validation Log

Date: 2026-06-22

Environment:

- OS: Windows
- Workspace: `D:\PERSONAL\chatgpt\skills\skill_graphic`
- Branch: `codex/skill-graphic-mvp`
- Reviewed base commit before this change: `6f6195b`
- Working tree during validation: dirty with the current function graph renderer changes
- Python: `3.14.0`
- SymPy: `1.14.0`
- jsonschema: `4.25.1`
- Playwright: `1.59.1` via `npx playwright --version`

## Commands

```powershell
python scripts\pro_review_cycle.py self-test
python scripts\run_smoke_tests.py
```

Result:

```text
pro review cycle self-test passed
D:\PERSONAL\chatgpt\skills\skill_graphic\dist\surface-revolution.html
D:\PERSONAL\chatgpt\skills\skill_graphic\dist\indefinite-integral-tan-sin.html
D:\PERSONAL\chatgpt\skills\skill_graphic\dist\_tmp-smoke-output.html
D:\PERSONAL\chatgpt\skills\skill_graphic\dist\_tmp-smoke-output.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\surface-revolution.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.math.json
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.render.json
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\indefinite-integral-tan-sin.html
```

Exit code: `0`

```powershell
python C:\Users\casti\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```

Result:

```text
Skill is valid!
```

Exit code: `0`

```powershell
python scripts\serve_dist.py --port 8766
playwright screenshot --viewport-size="1280,780" "http://127.0.0.1:8766/dist/surface-revolution.html?t=0.59" docs\review\screenshots\surface-revolution.png
playwright screenshot --viewport-size="1280,780" "http://127.0.0.1:8766/dist/indefinite-integral-tan-sin.html?t=0.36" docs\review\screenshots\integral-graphic.png
npx playwright screenshot --viewport-size=1280,780 --wait-for-timeout=800 "http://127.0.0.1:8767/dist/function-graph-cubic.html?t=0.42" docs\review\screenshots\function-graph-cubic.png
npx playwright screenshot --viewport-size=390,760 --wait-for-timeout=800 "http://127.0.0.1:8767/dist/function-graph-cubic.html?t=0.72" docs\review\screenshots\function-graph-cubic-mobile.png
```

Result:

```text
Created docs/review/screenshots/surface-revolution.png
Created docs/review/screenshots/integral-graphic.png
Created docs/review/screenshots/function-graph-cubic.png
Created docs/review/screenshots/function-graph-cubic-mobile.png
```

```text
Integrated browser check:
- URL: http://127.0.0.1:8767/dist/function-graph-cubic.html
- next/prev scene sequence: axes -> curve -> trace -> curve
- maximum camera boundary delta: 0.0379740284383967
- derivative scene: derivative path opacity 0.998312 and inside SVG viewport
- primitive scene: `curve-antiderivative-0` has class `curve antiderivative primitive support`, stroke `rgb(124, 58, 237)`, opacity `0.999711` near scene end, and a visible bounding box inside the SVG viewport
- primitive reload: `?ms=7500` renders the primitive caption directly, avoiding normalized-fraction drift on reload
- mobile 390x760: caption/formula/footer do not overlap
- curve paths: 3
- timeline: present
- formula panel: present
- render model marker: present
- console errors/warnings: 0
```

## What The Smoke Test Covers

- Schema validity.
- Positive math validation for:
  - surface revolution;
  - function graph cubic;
  - indefinite integral.
- Expected math check comparison where fixtures declare expected checks.
- Recursive expected-math subset comparison for declared formula fields.
- Function graph render-model compilation for curves, viewport, special points, intervals, tangents, and timeline.
- HTML generation for the three current visual demos.
- Function graph SVG renderer includes a draggable timeline, formula overlay, camera motion, tangent/extrema scenes, derivative and primitive layers.
- Function graph navigation uses exact millisecond scene jumps for prev/next, avoiding boundary drift from normalized timeline fractions.
- Function graph camera targets are compiled from render-model viewports per curve, so the derivative scene frames the whole derivative curve.
- Function graph antiderivative keeps its semantic id and also receives the `primitive` visual class, so the primitive curve has an explicit stroke.
- Rejection of negative fixtures:
- inverted surface domain: `domain_is_valid`;
- false extremum: `declared_points_match_function`;
- false inflection: `declared_points_match_function`;
- omitted asymptote: `declared_asymptotes_match_function`;
- tangent missing point: contract message contains `requires args.point_id`;
- extrema target wrong kind: contract message contains `incompatible targets`;
- duplicate feature id: contract message contains `Duplicate id`;
- asymptote action missing target: contract message contains `requires asymptote targets`.
- Rejection of stale `math_result` files by `contract_hash`.
- Live revalidation inside the generator even when `--math-result` is supplied.
- Ignoring forged `math_result` contents with a correct `contract_hash` by using the live validation result for render data.

## Artifact Hashes

```text
SHA256 f03ef779c353f5d52ef37e3fcfb89685948f70510752db10e4469904bb8a2047  dist/surface-revolution.html
SHA256 84c9d48284154372e05f94e507cf00a8850bb42cc5d54327b7b181cf637bd1cd  dist/surface-revolution.math.json
SHA256 948b672357287fc4190c2adc66f207fd336882528cef9e04569792c04a4af7a7  dist/function-graph-cubic.math.json
SHA256 075766591155a7abe5ed5c29daeaad9b9a4df9fd75e31895410d2ce946be8cac  dist/function-graph-cubic.render.json
SHA256 00259beeece145e66e43d4aec20a030c657012e8c68d04e702999ee301e35d9b  dist/function-graph-cubic.html
SHA256 2a36dbda47a09fcd7ba4b17ebddd2433c492389c31552403cec07548d7e458f9  dist/indefinite-integral-tan-sin.html
SHA256 7a2d49eb612b8b3e577eb47fb19c71198dadda50adbf3afdb89257e4ecba023a  dist/indefinite-integral-tan-sin.math.json
SHA256 19dcb593ba5f2da838643f138bca30dbc466928f8e7ff2ce2c9a6e06fb077016  docs/review/screenshots/function-graph-cubic.png
SHA256 dc52b1ff1d170eaf2036468c49ef7ca78840f62432afd3fb52bc53955fc3e79a  docs/review/screenshots/function-graph-cubic-mobile.png
SHA256 79a7734f52e4fd9d93bc7d96fb311b4eb0bfbe9211d1e84dfa053613c5770d2b  docs/review/screenshots/function-graph-cubic-primitive.png
```

## What It Does Not Cover Yet

- JavaScript console errors in CI.
- Timeline dragging in committed CI browser tests.
- Mobile/tablet screenshot comparison beyond the current function fixture browser capture.
- Broad `function_graph.html` coverage for asymptotes, discontinuities, multiple functions, and more camera plans.

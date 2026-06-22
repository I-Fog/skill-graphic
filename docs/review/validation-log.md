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

## Additional Validation After Pro Workflow Update

Date: 2026-06-22

Commands:

```powershell
npm install --save-dev @playwright/test
npx playwright install chromium
npx playwright --version
python scripts\pro_review_cycle.py self-test
python scripts\pro_review_cycle.py pack --dry-run --scope pro-loop --focus "Smoke compact pack"
python scripts\pro_review_cycle.py create --dry-run --packet full --focus "Smoke full pack"
python scripts\run_smoke_tests.py
python C:\Users\casti\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
git diff --check
$env:FUNCTION_GRAPH_URL="http://127.0.0.1:8774/dist/function-graph-cubic.html"
npm run test:function-graph -- --reporter=list
Remove-Item Env:\FUNCTION_GRAPH_URL -ErrorAction SilentlyContinue
```

Result:

```text
Playwright: Version 1.61.0
pro review cycle self-test passed
compact scoped packet dry-run generated
full packet dry-run generated
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\surface-revolution.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.math.json
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.render.json
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\indefinite-integral-tan-sin.html
Skill is valid!
git diff --check: exit code 0; PowerShell reported only the expected CRLF warning for .gitignore
function graph browser spec: 5 passed
```

The committed browser spec covers exact scene navigation, half-open scene boundaries, visible derivative and primitive curves, reload state preservation, and mobile overlay separation.

## Additional Validation After Packet Snapshot Update

Date: 2026-06-22

Commands:

```powershell
python -m py_compile scripts\pro_review_cycle.py scripts\run_smoke_tests.py
python scripts\pro_review_cycle.py self-test
python scripts\run_smoke_tests.py
python C:\Users\casti\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
python scripts\pro_review_cycle.py pack --dry-run --scope pro-loop --focus "Smoke compact pack"
python scripts\pro_review_cycle.py create --dry-run --packet full --focus "Smoke full pack"
python scripts\pro_review_cycle.py pack --round-id tmp-packet-inspect --scope pro-loop --focus "Inspect packet snapshot"
$env:FUNCTION_GRAPH_URL="http://127.0.0.1:8775/dist/function-graph-cubic.html"
npm run test:function-graph -- --reporter=list
Remove-Item Env:\FUNCTION_GRAPH_URL -ErrorAction SilentlyContinue
```

Result:

```text
pro review cycle self-test passed
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\surface-revolution.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.math.json
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.render.json
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\indefinite-integral-tan-sin.html
Skill is valid!
compact dry-run includes FILES_INCLUDED for scope pro-loop
full dry-run includes FILES_INCLUDED with [git-dirty-patch] and response scope all
temporary packet snapshot wrote packet/manifest.json, scoped.diff, copied 7 files, and round.json packet_snapshot
function graph browser spec: 5 passed
```

The Pro review contract now requires `SCOPE_REVISADO`, lists `FILES_INCLUDED` in every packet, and writes a reproducible `packet/` snapshot for non-dry-run rounds.

## Global Supervisor Extraction

Date: 2026-06-22

Created global skill:

```text
C:\Users\casti\.codex\skills\codex-pro-supervisor
```

Configured this repo with:

```text
codex-supervision.json
.codex-supervision/
```

External Pro review round:

```text
C:\Users\casti\.codex\skills\codex-pro-supervisor\.codex-supervision\pro-rounds\pro-global-supervision-01
```

Pro dictamen: `cambios solicitados`. Main P0 findings were unsafe path scope escape, missing secret preflight, self-packaging risk, missing packet hash binding, and too-silent `current-work` behavior outside Git. Implemented the first hardening pass before adoption.

Commands:

```powershell
python -m py_compile C:\Users\casti\.codex\skills\codex-pro-supervisor\scripts\supervise.py
python C:\Users\casti\.codex\skills\codex-pro-supervisor\scripts\supervise.py self-test
python C:\Users\casti\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\casti\.codex\skills\codex-pro-supervisor
python C:\Users\casti\.codex\skills\codex-pro-supervisor\scripts\supervise.py pack --dry-run --scope .
python C:\Users\casti\.codex\skills\codex-pro-supervisor\scripts\supervise.py pack --dry-run --scope current-work
python scripts\pro_review_cycle.py self-test
python scripts\run_smoke_tests.py
python C:\Users\casti\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```

Result:

```text
global supervisor py_compile: OK
global supervisor self-test: OK
global supervisor skill validation: Skill is valid!
global supervisor --scope . dry-run: OK, emits FILES_INCLUDED and PACKET_SHA256
global supervisor current-work outside Git: blocked as expected
global supervisor secret preflight with .env.supervisor-test: blocked as expected
local pro_review_cycle self-test: OK
skill_graphic smoke tests: OK
skill_graphic quick_validate: Skill is valid!
```

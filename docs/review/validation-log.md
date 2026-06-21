# Validation Log

Date: 2026-06-21

Environment:

- OS: Windows
- Workspace: `D:\PERSONAL\chatgpt\skills\skill_graphic`
- Branch: `codex/skill-graphic-mvp`
- Reviewed base commit before this change: `6f6195b`
- Working tree during validation: dirty with the current review-fix changes
- Python: `3.14.0`
- SymPy: `1.14.0`
- jsonschema: `4.25.1`
- Playwright: `1.59.1` via `npx playwright --version`

## Commands

```powershell
python scripts\run_smoke_tests.py
```

Result:

```text
D:\PERSONAL\chatgpt\skills\skill_graphic\dist\surface-revolution.html
D:\PERSONAL\chatgpt\skills\skill_graphic\dist\indefinite-integral-tan-sin.html
D:\PERSONAL\chatgpt\skills\skill_graphic\dist\_tmp-smoke-output.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\surface-revolution.html
Smoke tests passed: D:\PERSONAL\chatgpt\skills\skill_graphic\dist\function-graph-cubic.math.json
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
```

Result:

```text
Created docs/review/screenshots/surface-revolution.png
Created docs/review/screenshots/integral-graphic.png
```

## What The Smoke Test Covers

- Schema validity.
- Positive math validation for:
  - surface revolution;
  - function graph cubic;
  - indefinite integral.
- Expected math check comparison where fixtures declare expected checks.
- Recursive expected-math subset comparison for declared formula fields.
- HTML generation for the two current visual demos.
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
SHA256 2a36dbda47a09fcd7ba4b17ebddd2433c492389c31552403cec07548d7e458f9  dist/indefinite-integral-tan-sin.html
SHA256 7a2d49eb612b8b3e577eb47fb19c71198dadda50adbf3afdb89257e4ecba023a  dist/indefinite-integral-tan-sin.math.json
```

## What It Does Not Cover Yet

- JavaScript console errors in CI.
- Timeline dragging in automated browser tests.
- Mobile/tablet screenshot comparison.
- Generic `function_graph.html`, because it does not exist yet.

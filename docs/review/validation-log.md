# Validation Log

Date: 2026-06-21

Environment:

- OS: Windows
- Workspace: `D:\PERSONAL\chatgpt\skills\skill_graphic`
- Branch: `codex/skill-graphic-mvp`

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

```powershell
python C:\Users\casti\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```

Result:

```text
Skill is valid!
```

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
- HTML generation for the two current visual demos.
- Rejection of negative fixtures:
  - inverted surface domain;
  - false extremum;
  - false inflection;
  - omitted asymptote/discontinuity.
- Rejection of stale `math_result` files by `contract_hash`.

## What It Does Not Cover Yet

- JavaScript console errors in CI.
- Timeline dragging in automated browser tests.
- Mobile/tablet screenshot comparison.
- Generic `function_graph.html`, because it does not exist yet.

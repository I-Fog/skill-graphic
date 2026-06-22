## Project Purpose

This repo defines a Codex skill and runtime scaffold for exact, interactive educational simulations.

## Durable Workflow

- Treat `schemas/simulation.schema.json` as the source contract for simulations.
- Keep math validation separate from rendering. Renderers must draw from validated definitions, not invent geometry.
- Treat `scripts/generate_simulation.py` as a validation gate. It must reject stale `math_result` files whose `contract_hash` does not match the input JSON.
- The generator must always rerun `validate_math`; a provided `math_result` is only an untrusted cache candidate.
- Function features use typed ids. Scene targets must be compatible with the action (`show_extrema` -> extremum points, `show_asymptote` -> asymptote entities, etc.).
- Negative fixtures must include `expected_failure` so smoke tests verify the intended phase/check/message instead of accepting any exception.
- Scene actions that affect specific objects should use explicit `targets` or `args`.
- Use `examples/surface-revolution/input.json` as the canonical first fixture.
- Use `references/functions.md` and `examples/function-graph-cubic/input.json` when changing the reusable function graph contract.
- Prefer Python scripts for deterministic validation/generation until a TypeScript build pipeline exists.
- Generated HTML belongs in `dist/`; do not put generated outputs inside `references/` or `assets/`.
- The canonical surface-of-revolution fixture uses one SVG stage with projected 3D geometry. Do not reintroduce a separate `three-root` panel.
- During `rotate_curve_into_surface`, the curve rotation and camera/viewbox movement happen together.
- The surface mesh must be born from the curve: the `theta = 0` generatrix coincides with the green function curve.
- Keep formulas in the floating `formula-panel` overlay with fade behavior; do not restore the removed lower formula/checks band.
- Keep the timeline as a draggable scrubber so the user can move backward and forward with the cursor.
- Serve generated HTML over local HTTP for browser validation:
  `python scripts/serve_dist.py`
- Use compact scoped Pro packets by default. Prefer the global supervisor so the workflow stays reusable across repos:
  `codex-supervise run --transport uia --scope function-renderer`
- If the terminal has not reloaded PATH yet, use:
  `& "$env:USERPROFILE\.codex\bin\codex-supervise.cmd" run --transport uia --scope function-renderer`
- Keep `python scripts/pro_review_cycle.py ...` only as the repo-specific compatibility route.
- Keep `codex-supervision.json` aligned with durable project review scopes.
- Use `--scope pro-loop`, `--scope function-renderer`, `--scope docs`, or `--scope all` to match the review target. Use `--packet full` only for broad audits where Pro needs the full dirty diff.
- Every Pro round must include `FILES_INCLUDED`, require `SCOPE_REVISADO` and `PACKET_SHA256` in the answer, and write a reproducible `packet/` snapshot with `packet/manifest.json`, copied files, and the packet diff.
- If UIA cannot access ChatGPT, use `codex-supervise pack --scope <scope> --copy` plus `codex-supervise ingest <round-id> --from-clipboard`. Finish completed rounds with `codex-supervise verify <round-id>`. Global round artifacts live in `.codex-supervision/pro-rounds/`.
- Use `npm run test:function-graph` for the versioned browser regression check of the function renderer. Serve `dist/` first and set `FUNCTION_GRAPH_URL` if not using port 8765.

## Validation

- Run the skill validator after `SKILL.md` changes:
  `python C:\Users\casti\.codex\skills\.system\skill-creator\scripts\quick_validate.py .`
- Run the project smoke check after schema, validator, renderer, or example changes:
  `python scripts/run_smoke_tests.py`
- For browser validation, open:
  `http://127.0.0.1:8765/dist/surface-revolution.html`

## Browser Automation

- Use Playwright headless by default for browser checks and visual validation.

## Spanish Comments

- When adding Spanish code comments, keep them natural and student-like. Prefer "dejamos", "miramos", "usamos", or direct explanation over impersonal manual wording.

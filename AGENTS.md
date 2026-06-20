## Project Purpose

This repo defines a Codex skill and runtime scaffold for exact, interactive educational simulations.

## Durable Workflow

- Treat `schemas/simulation.schema.json` as the source contract for simulations.
- Keep math validation separate from rendering. Renderers must draw from validated definitions, not invent geometry.
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

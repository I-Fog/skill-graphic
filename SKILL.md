---
name: skill-graphic
description: Create exact interactive educational simulations from declarative math or science scene contracts. Use when Codex needs to generate, validate, or refine browser-based animated explainers for calculus, physics, electronics, statistics, surfaces of revolution, graphs, formulas, camera motion, or stepwise simulations with SVG, Three.js, SymPy, and Playwright checks.
---

# Skill Graphic

Use this skill to turn a study or teaching request into an exact interactive browser simulation.

## Core Rule

Define the mathematical or scientific model first, validate it, then render it. Do not make a renderer invent formulas, domains, geometry, units, or physical conditions.

Canonical flow:

```text
request -> simulation JSON -> schema validation -> math/domain validation -> HTML generation -> browser/visual check
```

## Fast Path

1. Write or update a simulation JSON that follows `schemas/simulation.schema.json`.
2. Use `examples/surface-revolution/input.json` as the first reference for surfaces of revolution.
3. Run:

```powershell
python scripts/run_smoke_tests.py
```

4. For a single generated artifact, run:

```powershell
python scripts/generate_simulation.py examples/surface-revolution/input.json dist/surface-revolution.html
```

5. Serve generated files when the HTML imports local ES modules:

```powershell
python scripts/serve_dist.py
```

6. Return the local URL or absolute HTML path and mention the validation command used.

## Contract Boundaries

- Put durable simulation fields in `schemas/simulation.schema.json`.
- Put domain examples in `examples/`.
- Put reusable rendering templates in `assets/templates/`.
- Put math validation in `python/validator/`.
- Put generated HTML in `dist/`.
- Keep generated logs, screenshots, temporary traces, and rejected outputs outside references and assets.

## Renderer Choices

- Use SVG for 2D axes, curves, graph annotations, labels, intervals, and formulas.
- Use Three.js for 3D surfaces, solids, camera motion, fields, and rotations.
- Use SymPy for derivatives, integrals, parametrizations, simplifications, and model checks.
- Use Playwright headless for final browser validation when visual correctness matters.

## Scene Design

Model each simulation as ordered scenes. Each scene needs one learning goal and one visual action.

Useful actions:

- `draw_axes`
- `draw_curve`
- `highlight_interval`
- `show_rotation_axis`
- `rotate_curve_into_surface`
- `move_camera`
- `show_formula`
- `show_validation`

## Minimum Acceptance

A simulation is not done until:

- the JSON validates against the schema;
- the relevant math checks pass;
- generated HTML opens as a single interactive page;
- controls support play, pause, replay, previous, next, and speed when practical;
- formulas and labels refer to visible objects;
- the renderer uses model-derived geometry;
- desktop and mobile layouts have no obvious blank stage or clipped core controls.

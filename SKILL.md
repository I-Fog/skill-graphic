---
name: skill-graphic
description: Create exact interactive educational simulations from declarative math or science scene contracts. Use when Codex needs to generate, validate, or refine browser-based animated explainers for calculus, functions, physics, electronics, statistics, surfaces of revolution, graphs, formulas, camera motion, scrubber timelines, or stepwise simulations with SVG, projected 3D geometry, SymPy, and Playwright checks.
---

# Skill Graphic

Use this skill to turn a study or teaching request into an exact interactive browser simulation.

## Core Rule

Define the mathematical or scientific model first, validate it, then render it. Do not make a renderer invent formulas, domains, geometry, units, or physical conditions.

Canonical flow:

```text
request -> simulation JSON -> schema validation -> math/domain validation -> HTML generation -> browser/visual check
```

`scripts/generate_simulation.py` is a validation gate, not a blind renderer. It must reject stale, failed, mismatched, or missing math validation using the simulation `contract_hash`.

## Fast Path

1. Write or update a simulation JSON that follows `schemas/simulation.schema.json`.
2. Use `examples/surface-revolution/input.json` as the first reference for surfaces of revolution.
3. Use `references/functions.md` before creating or modifying a `function_graph` simulation.
4. Use `examples/function-graph-cubic/input.json` as the first reference for function graph simulations.
5. Use `references/integrals.md` before creating or modifying an `indefinite_integral` simulation.
6. Use `examples/indefinite-integral-tan-sin/input.json` as the first reference for trigonometric indefinite integrals.
7. Run:

```powershell
python scripts/run_smoke_tests.py
```

8. For a single generated artifact, run:

```powershell
python scripts/generate_simulation.py examples/surface-revolution/input.json dist/surface-revolution.html
```

9. Serve generated files for browser validation:

```powershell
python scripts/serve_dist.py
```

10. Return the local URL or absolute HTML path and mention the validation command used.

## Contract Boundaries

- Put durable simulation fields in `schemas/simulation.schema.json`.
- Put domain examples in `examples/`.
- Put reusable rendering templates in `assets/templates/`.
- Put math validation in `python/validator/`.
- Put generated HTML in `dist/`.
- Keep generated logs, screenshots, temporary traces, and rejected outputs outside references and assets.

## Renderer Choices

- Use SVG for axes, curves, graph annotations, labels, intervals, formulas, and the canonical projected-3D surface fixture.
- Keep the surface-of-revolution MVP in one visual stage. Do not add a second 3D panel for this fixture.
- When `rotate_curve_into_surface` runs, animate the angle parameter and the camera/viewbox in the same scene.
- Ensure the generated surface starts from the drawn curve: at `theta = 0`, the projected surface generatrix must coincide with the green function curve.
- Use a full 3D renderer only when the simulation contract and template explicitly require it.
- Use SymPy for derivatives, integrals, parametrizations, simplifications, and model checks.
- Use Playwright headless for final browser validation when visual correctness matters.
- For function exercises, read `references/functions.md` and validate domain, derivative, primitive, points, asymptotes, and discontinuities before rendering.
- For integral exercises, read `references/integrals.md` and choose the smallest method that makes the transformation exact.

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

Function graph actions:

- `draw_function_graph`
- `trace_point`
- `show_tangent`
- `show_extrema`
- `show_inflection`
- `show_asymptote`
- `show_discontinuity`
- `show_derivative_graph`
- `show_antiderivative_graph`
- `compare_function_and_derivative`

Integral actions:

- `draw_integrand_graph`
- `sweep_signed_area`
- `draw_primitive_curve`
- `show_primitive_family`
- `introduce_substitution`
- `transform_integrand`
- `split_partial_fractions`
- `integrate_terms`
- `back_substitute`
- `verify_derivative`

## Minimum Acceptance

A simulation is not done until:

- the JSON validates against the schema;
- the relevant math checks pass;
- required checks for the simulation type and scene actions are present;
- any math result used by the generator matches the current contract hash;
- generated HTML opens as a single interactive page;
- controls support play, pause, replay, previous, next, speed, and a draggable timeline scrubber when practical;
- formulas and labels refer to visible objects;
- formulas appear in a floating overlay with fade-in/fade-out, not in a permanent lower band;
- axis labels appear only after their axes finish drawing;
- the renderer uses model-derived geometry;
- desktop and mobile layouts have no obvious blank stage or clipped core controls.

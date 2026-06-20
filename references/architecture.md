# Architecture

## Source Of Truth

The simulation JSON is the source of truth. It defines parameters, formulas, domains, scene actions, controls, and required checks.

## Layers

1. Schema validation checks the contract shape.
2. Math validation checks symbolic assumptions with SymPy.
3. Generation converts the validated contract into browser HTML.
4. Rendering uses SVG for exact diagrams and the canonical projected-3D surface-of-revolution fixture.
5. Visual validation opens the generated artifact and checks controls, SVG, timeline scrubbing, camera framing, and layout.

## Non-Negotiables

- Keep mathematical definitions out of renderers.
- Keep generated artifacts in `dist/`.
- Add a fixture before adding a new simulation type.
- Extend the schema before relying on new JSON fields.
- Add a validator check for every new fragile assumption.
- For the canonical surface-of-revolution fixture, keep a single visual stage. The 3D surface projection, axes, function curve, labels, and rotation mesh live in the same SVG.
- The camera/viewbox motion is part of the surface scene, so rotation and paneo can be scrubbed together.
- Floating formulas are transient overlays; permanent bottom bands are not part of the current output contract.

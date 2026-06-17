# Architecture

## Source Of Truth

The simulation JSON is the source of truth. It defines parameters, formulas, domains, scene actions, controls, and required checks.

## Layers

1. Schema validation checks the contract shape.
2. Math validation checks symbolic assumptions with SymPy.
3. Generation converts the validated contract into browser HTML.
4. Rendering uses SVG for exact 2D diagrams and Three.js for 3D geometry.
5. Visual validation opens the generated artifact and checks controls, canvas, SVG, and layout.

## Non-Negotiables

- Keep mathematical definitions out of renderers.
- Keep generated artifacts in `dist/`.
- Add a fixture before adding a new simulation type.
- Extend the schema before relying on new JSON fields.
- Add a validator check for every new fragile assumption.

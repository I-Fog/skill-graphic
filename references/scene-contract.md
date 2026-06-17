# Scene Contract

Each scene represents one conceptual step. Avoid scenes that combine multiple learning goals.

## Required Fields

- `id`: stable hyphen-case identifier.
- `goal`: what the learner should understand.
- `action`: renderer instruction.

## Optional Fields

- `duration_ms`: default animation duration for the scene.
- `caption`: short in-frame explanation.
- `formula`: TeX-like expression shown in the detail block.

## MVP Actions

- `draw_axes`: reveal the coordinate system.
- `draw_curve`: stroke-draw the function over its domain.
- `highlight_interval`: mark endpoints or bounds.
- `show_rotation_axis`: emphasize the axis that remains fixed.
- `rotate_curve_into_surface`: animate the angle parameter and surface mesh.
- `move_camera`: change viewpoint without changing the model.
- `show_formula`: reveal a formula tied to the visible object.
- `show_validation`: summarize the checks that passed.

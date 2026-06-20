# Surface Revolution Canonical Fixture

This fixture covers the first MVP target: a curve rotated around `OX`.

Input problem:

```text
a > 0
y = x sqrt(x/a)
0 <= x <= a
rotation axis: OX
```

Required visual moments:

1. Draw Cartesian axes.
2. Draw the curve.
3. Mark the interval endpoints.
4. Highlight the rotation axis.
5. Rotate the curve into a surface while the camera moves.
6. Reveal the area formula and validation summary.

Current rendering contract:

- Use one visual stage, not a separate 2D/3D split.
- The surface mesh starts from the drawn curve.
- Rotation and camera movement happen during the same scene.
- The timeline can scrub backward and forward.
- Formula and validation text appear as transient floating overlays.

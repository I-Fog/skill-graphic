# Function Graph Canonical Fixture

Input function:

```text
f(x) = x^3 - 3x
domain: [-2.2, 2.2]
```

Required validation targets:

1. Parse the function.
2. Validate the visual domain.
3. Validate `f'(x) = 3x^2 - 3`.
4. Validate `F(x) = x^4/4 - 3x^2/2`.
5. Validate roots, extrema, and inflection point.

Current scope:

- This fixture strengthens the reusable function contract and math validator.
- It intentionally does not require generated HTML until the generic function graph renderer is implemented.

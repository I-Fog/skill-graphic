# Function Graph Simulations

Use this reference when the request is about understanding, drawing, transforming, comparing, deriving, or integrating functions on a Cartesian plane.

## Contract

Use simulation type `function_graph`.

Required math fields:

- `function`: source expression in SymPy-compatible syntax.
- `variable`: graph variable.
- `domain`: visual interval `[start, end]`.

Optional math fields:

- `derivative`: expected derivative. Validate it when used for tangents or derivative graphs.
- `antiderivative`: expected primitive. Validate it when used for accumulated area or primitive graphs.
- `anchor`: base point for accumulated quantities.

Optional `features`:

- `special_points`: roots, intersections, extrema, inflection points, or custom highlighted points.
- `highlighted_intervals`: intervals for increasing/decreasing, sign, area, or custom emphasis.
- `vertical_asymptotes`: typed entities `{id, kind: "vertical", x, label?}`.
- `discontinuities`: typed entities `{id, kind, x, label?}`, where `kind` is `removable`, `jump`, `essential`, or `custom`.

Scene actions that affect a concrete feature must identify it with compatible `targets` or `args`:

- `show_tangent` requires `args.point_id` that refers to a `special_points` id.
- `show_extrema` targets only points with `kind: "extremum"`.
- `show_inflection` targets only points with `kind: "inflection"`.
- `show_asymptote` targets only `vertical_asymptotes` ids.
- `show_discontinuity` targets only `discontinuities` ids.
- `highlight_interval` targets only `highlighted_intervals` ids.

Ids must be unique across scenes and feature collections.

## Scene Pattern

Prefer this order when the user has not specified a different pedagogy:

1. Draw axes and the visual domain.
2. Draw the function curve smoothly.
3. Move a point along the curve.
4. Show local information: coordinate, tangent, slope, sign, or interval.
5. Mark global features: roots, extrema, inflection points, asymptotes, discontinuities.
6. Add derivative or primitive curves only after the original function is established.
7. Compare related functions or transformations.
8. Show the symbolic check that justifies the highlighted feature.

## Actions

- `draw_function_graph`: draw the source curve.
- `trace_point`: move a point along the curve and update coordinates.
- `show_tangent`: draw the tangent line and slope at `args.point_id` or a targeted point.
- `show_extrema`: highlight targeted maxima or minima.
- `show_inflection`: highlight targeted changes of concavity.
- `show_asymptote`: draw and label targeted asymptotes.
- `show_discontinuity`: mark targeted holes or jumps.
- `show_derivative_graph`: draw `f'(x)` as a related curve.
- `show_antiderivative_graph`: draw a primitive or accumulated-area curve.
- `compare_function_and_derivative`: connect signs/slopes between `f` and `f'`.

## Validation

Do not render a function simulation until the relevant checks pass:

- expression parses;
- visual domain is ordered;
- declared derivative differentiates back from `f`;
- declared antiderivative differentiates to `f`;
- declared points lie on the function when they include y-values;
- roots/extrema/inflection labels satisfy the corresponding equations;
- declared vertical asymptotes have infinite one-sided behavior or a zero denominator;
- declared discontinuities are singular points of the expression.

## Rendering Notes

- Treat the Cartesian plot as the main object.
- Keep symbolic formulas as overlays or side support.
- Do not invent special points in the renderer; use validated `features`.
- Keep camera/viewBox decisions separate from mathematical sampling.

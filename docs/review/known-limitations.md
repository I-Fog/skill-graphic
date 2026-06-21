# Known Limitations

## Generic Engine

- `function_graph.html` is not implemented yet.
- The first `function_graph` render-model compiler exists for continuous Cartesian function fixtures, but it is not yet connected to a generic HTML renderer.
- Surface and integral demos still use template-specific rendering logic.
- The integral visual primitive is sampled numerically in the browser demo, although the validator knows an exact primitive.

## Contract

- The schema is not yet split into `$defs` and `oneOf`.
- Scene `args` are narrowed and targets are typed semantically, but JSON Schema does not yet encode every action-specific shape with `oneOf`.
- Checks are enforced semantically in `python/validator/contract.py`, not directly by JSON Schema.
- Display formulas such as `scene.formula` and integral `antiderivative` are pedagogical text; `antiderivative_check` is the expression validated by SymPy until the contract moves to `{expression, display_tex}` pairs.

## Validation

- SymPy expression parsing is still string-based.
- Function interval validation samples interior points; it is stronger than before but not a full proof for every possible function.
- Asymptote/discontinuity detection is limited to symbolic denominator roots in current fixtures.
- Integral final antiderivative validation uses symbolic simplification with numeric fallback on the declared domain to handle log branch simplification.

## Browser Testing

- There is no committed Playwright test suite.
- Static screenshots are included for review, but they are not a replacement for CI.
- Smoothness and reversibility of timelines are not measured automatically.

## Security And Portability

- A restricted math parser or AST should replace direct SymPy parsing before accepting arbitrary untrusted contracts.
- Windows-specific validation paths still appear in local instructions and validation logs.

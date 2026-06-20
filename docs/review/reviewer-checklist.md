# Reviewer Checklist

Use this checklist when reviewing without executing tests.

## Contract

- Does `schemas/simulation.schema.json` expose enough structure for the next generic renderer?
- Are `targets` and `args` sufficient, or should actions have strict per-action schemas?
- Should `checks` be removed from fixtures and derived entirely by validators?
- Should type-specific schemas be moved to `$defs` + `oneOf` before adding more simulation types?

## Validation

- Are required checks in `python/validator/contract.py` complete for each simulation type?
- Do the negative fixtures cover the most important false-green cases?
- Which validators still rely too much on sampling?
- Where should a safe math expression parser replace `sympify`?

## Rendering Plan

- Should `python/compiler/function_graph.py` be the next artifact?
- What should the render model contain for curves, intervals, tangents, discontinuities, areas, and labels?
- Which visual layers should be shared by functions, integrals, and surfaces?
- What should remain template-specific after the generic Cartesian renderer exists?

## Browser Evidence

- Are the static screenshots sufficient for a human review pass?
- What Playwright checks should be added first?
- Which DOM or SVG invariants should be asserted before pixel screenshots?

## Merge Standard

- Is this branch acceptable as a scaffold MVP?
- What minimum changes are required before calling it a generic exact simulation skill?

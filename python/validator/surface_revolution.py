from __future__ import annotations

from typing import Any

import sympy as sp

try:
    from .sympy_utils import parse_surface_input, stringify
except ImportError:
    from sympy_utils import parse_surface_input, stringify


def validate_surface_of_revolution(simulation: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_surface_input(simulation)
    x = parsed.variable
    theta = sp.symbols("theta", real=True)
    f = sp.simplify(parsed.function)
    derivative = sp.simplify(sp.diff(f, x))

    if simulation["math"]["rotation_axis"] != "x":
        raise ValueError("MVP only supports rotation around the x axis.")

    surface = {
        "x": stringify(x),
        "y": stringify(f * sp.cos(theta)),
        "z": stringify(f * sp.sin(theta)),
    }

    area_integrand = sp.simplify(2 * sp.pi * f * sp.sqrt(1 + derivative**2))
    exact_area = sp.integrate(area_integrand, (x, parsed.domain_start, parsed.domain_end))
    domain_delta = sp.simplify(parsed.domain_end - parsed.domain_start)
    domain_ordered = domain_delta.is_positive is True or bool(sp.N(domain_delta.subs({symbol: 1 for symbol in parsed.parameters.values()})) > 0)
    derivative_samples = [
        parsed.domain_start + (parsed.domain_end - parsed.domain_start) * sp.Rational(index, 8)
        for index in range(1, 8)
    ]
    derivative_finite = all(
        value.is_finite is not False
        for value in (sp.simplify(derivative.subs(x, sample)) for sample in derivative_samples)
    )

    checks = {
        "domain_is_valid": domain_ordered,
        "derivative_exists_on_interval": derivative is not None and derivative_finite,
        "surface_parametrization_matches_axis": surface["x"] == stringify(x),
        "area_formula_matches_surface_of_revolution": sp.simplify(
            area_integrand - 2 * sp.pi * f * sp.sqrt(1 + derivative**2)
        ) == 0,
    }

    return {
        "id": simulation["id"],
        "type": simulation["type"],
        "function": stringify(f),
        "domain": [stringify(parsed.domain_start), stringify(parsed.domain_end)],
        "derivative": stringify(derivative),
        "surface_parametrization": surface,
        "area_integrand": stringify(area_integrand),
        "exact_area": stringify(exact_area),
        "checks": checks,
        "passed": all(checks[name] for name in simulation["checks"]),
    }

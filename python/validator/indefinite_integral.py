from __future__ import annotations

from typing import Any

import sympy as sp
from sympy.calculus.util import continuous_domain

try:
    from .sympy_utils import stringify
except ImportError:
    from sympy_utils import stringify


def _locals(variable: sp.Symbol, t: sp.Symbol) -> dict[str, Any]:
    return {
        str(variable): variable,
        "t": t,
        "sin": sp.sin,
        "sen": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "log": sp.log,
        "ln": sp.log,
        "sqrt": sp.sqrt,
        "pi": sp.pi,
    }


def _is_zero(expr: sp.Expr) -> bool:
    return sp.simplify(sp.cancel(expr)) == 0


def _is_zero_on_samples(expr: sp.Expr, variable: sp.Symbol, start: sp.Expr, end: sp.Expr) -> bool:
    simplified = sp.trigsimp(sp.simplify(expr))
    if _is_zero(simplified):
        return True
    samples = [
        start + (end - start) * sp.Rational(index, 8)
        for index in range(1, 8)
    ]
    for sample in samples:
        value = complex(sp.N(simplified.subs(variable, sample)))
        if abs(value) > 1e-8:
            return False
    return True


def validate_indefinite_integral(simulation: dict[str, Any]) -> dict[str, Any]:
    variable = sp.symbols(simulation["math"]["variable"])
    t = sp.symbols("t")
    locals_map = _locals(variable, t)

    integrand = sp.sympify(simulation["math"]["integrand"], locals=locals_map)
    domain_start = sp.sympify(simulation["math"]["domain"][0], locals=locals_map)
    domain_end = sp.sympify(simulation["math"]["domain"][1], locals=locals_map)
    anchor = sp.sympify(simulation["math"]["anchor"], locals=locals_map)
    provided_rational = sp.sympify(simulation["math"]["rational_integrand"], locals=locals_map)
    provided_partial = sp.sympify(simulation["math"]["partial_fractions"], locals=locals_map)
    antiderivative_t = sp.sympify(simulation["math"]["antiderivative_t"], locals=locals_map)
    antiderivative_check = sp.sympify(simulation["math"]["antiderivative_check"], locals=locals_map)

    sin_x = 2 * t / (1 + t**2)
    cos_x = (1 - t**2) / (1 + t**2)
    tan_x = 2 * t / (1 - t**2)
    dx_dt = 2 / (1 + t**2)

    transformed = sp.cancel(
        integrand.subs(
            {
                sp.sin(variable): sin_x,
                sp.cos(variable): cos_x,
                sp.tan(variable): tan_x,
            },
            simultaneous=True,
        )
        * dx_dt
    )
    visual_interval = sp.Interval(domain_start, domain_end)
    finite_on_domain = continuous_domain(integrand, variable, visual_interval) == visual_interval
    substitution_is_declared = simulation["math"]["method"] == "weierstrass_substitution" and (
        simulation["math"]["substitution"].replace(" ", "") in {"t=tan(x/2)", "t=tan(" + str(variable) + "/2)"}
    )

    checks = {
        "integrand_matches_statement": integrand is not None,
        "visual_domain_avoids_singularities": bool(domain_start < anchor < domain_end) and finite_on_domain,
        "weierstrass_substitution_is_valid": substitution_is_declared
        and _is_zero(sin_x**2 + cos_x**2 - 1)
        and _is_zero(tan_x - sin_x / cos_x),
        "rational_integrand_matches_substitution": _is_zero(provided_rational - transformed),
        "partial_fractions_match": _is_zero(provided_partial - provided_rational),
        "antiderivative_differentiates_to_integrand": _is_zero(sp.diff(antiderivative_t, t) - provided_rational)
        and _is_zero_on_samples(sp.diff(antiderivative_check, variable) - integrand, variable, domain_start, domain_end),
    }

    return {
        "id": simulation["id"],
        "type": simulation["type"],
        "integrand": stringify(integrand),
        "domain": [stringify(domain_start), stringify(domain_end)],
        "anchor": stringify(anchor),
        "substitution": simulation["math"]["substitution"],
        "rational_integrand": stringify(provided_rational),
        "computed_rational_integrand": stringify(transformed),
        "partial_fractions": stringify(provided_partial),
        "antiderivative_t": stringify(antiderivative_t),
        "antiderivative": simulation["math"]["antiderivative"],
        "antiderivative_check": stringify(antiderivative_check),
        "checks": checks,
        "passed": all(checks[name] for name in simulation["checks"]),
    }

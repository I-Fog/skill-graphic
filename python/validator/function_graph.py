from __future__ import annotations

from typing import Any

import sympy as sp

try:
    from .sympy_utils import stringify
except ImportError:
    from sympy_utils import stringify


def _locals(variable: sp.Symbol, parameters: dict[str, sp.Symbol]) -> dict[str, Any]:
    values: dict[str, Any] = {
        str(variable): variable,
        "sin": sp.sin,
        "sen": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "log": sp.log,
        "ln": sp.log,
        "sqrt": sp.sqrt,
        "exp": sp.exp,
        "pi": sp.pi,
        "E": sp.E,
    }
    values.update(parameters)
    return values


def _is_zero(expr: sp.Expr) -> bool:
    return sp.simplify(sp.cancel(expr)) == 0


def _is_finite_number(expr: sp.Expr) -> bool:
    try:
        value = complex(sp.N(expr))
    except TypeError:
        return False
    return abs(value) < 1e8 and value.real == value.real and value.imag == value.imag


def _parse_parameters(simulation: dict[str, Any]) -> tuple[dict[str, sp.Symbol], dict[sp.Symbol, sp.Expr]]:
    symbols: dict[str, sp.Symbol] = {}
    numeric_values: dict[sp.Symbol, sp.Expr] = {}
    for name, payload in simulation.get("parameters", {}).items():
        symbol = sp.symbols(name, real=True)
        symbols[name] = symbol
        numeric_values[symbol] = sp.sympify(payload["value"])
    return symbols, numeric_values


def _points_match(
    features: dict[str, Any],
    x: sp.Symbol,
    function: sp.Expr,
    derivative: sp.Expr,
    second_derivative: sp.Expr,
    locals_map: dict[str, Any],
) -> bool:
    for point in features.get("special_points", []):
        px = sp.sympify(point["x"], locals=locals_map)
        fx = sp.simplify(function.subs(x, px))
        if "y" in point and not _is_zero(fx - sp.sympify(point["y"], locals=locals_map)):
            return False
        kind = point["kind"]
        if kind == "root" and not _is_zero(fx):
            return False
        if kind == "extremum" and not _is_zero(derivative.subs(x, px)):
            return False
        if kind == "inflection" and not _is_zero(second_derivative.subs(x, px)):
            return False
    return True


def _asymptotes_match(
    features: dict[str, Any],
    x: sp.Symbol,
    function: sp.Expr,
    locals_map: dict[str, Any],
) -> bool:
    numerator, denominator = sp.fraction(sp.cancel(function))
    del numerator
    for raw in features.get("vertical_asymptotes", []):
        value = sp.sympify(raw, locals=locals_map)
        denominator_zero = _is_zero(denominator.subs(x, value))
        left_limit = sp.limit(function, x, value, dir="-")
        right_limit = sp.limit(function, x, value, dir="+")
        infinite_limit = left_limit in (sp.oo, -sp.oo) or right_limit in (sp.oo, -sp.oo)
        if not denominator_zero and not infinite_limit:
            return False
    return True


def _discontinuities_match(
    features: dict[str, Any],
    x: sp.Symbol,
    function: sp.Expr,
    locals_map: dict[str, Any],
) -> bool:
    for raw in features.get("discontinuities", []):
        value = sp.sympify(raw, locals=locals_map)
        direct = function.subs(x, value)
        if direct.is_finite is True and _is_finite_number(direct):
            return False
    return True


def validate_function_graph(simulation: dict[str, Any]) -> dict[str, Any]:
    variable = sp.symbols(simulation["math"]["variable"], real=True)
    parameter_symbols, parameter_values = _parse_parameters(simulation)
    locals_map = _locals(variable, parameter_symbols)
    math = simulation["math"]
    features = simulation.get("features", {})

    function = sp.sympify(math["function"], locals=locals_map)
    domain_start = sp.sympify(math["domain"][0], locals=locals_map).subs(parameter_values)
    domain_end = sp.sympify(math["domain"][1], locals=locals_map).subs(parameter_values)
    function_for_checks = function.subs(parameter_values)
    derivative = sp.simplify(sp.diff(function, variable))
    derivative_for_checks = derivative.subs(parameter_values)
    second_derivative = sp.simplify(sp.diff(derivative, variable)).subs(parameter_values)

    declared_derivative = (
        sp.sympify(math["derivative"], locals=locals_map)
        if "derivative" in math
        else None
    )
    declared_antiderivative = (
        sp.sympify(math["antiderivative"], locals=locals_map)
        if "antiderivative" in math
        else None
    )

    checks = {
        "function_expression_is_valid": function is not None,
        "visual_domain_is_ordered": bool(sp.N(domain_start) < sp.N(domain_end)),
        "derivative_matches_function": declared_derivative is None
        or _is_zero(declared_derivative - derivative),
        "antiderivative_matches_function": declared_antiderivative is None
        or _is_zero(sp.diff(declared_antiderivative, variable) - function),
        "declared_points_match_function": _points_match(
            features,
            variable,
            function_for_checks,
            derivative_for_checks,
            second_derivative,
            locals_map,
        ),
        "declared_asymptotes_match_function": _asymptotes_match(
            features,
            variable,
            function_for_checks,
            locals_map,
        ),
        "declared_discontinuities_match_function": _discontinuities_match(
            features,
            variable,
            function_for_checks,
            locals_map,
        ),
    }

    return {
        "id": simulation["id"],
        "type": simulation["type"],
        "function": stringify(function),
        "domain": [stringify(domain_start), stringify(domain_end)],
        "derivative": stringify(derivative),
        "antiderivative": stringify(declared_antiderivative) if declared_antiderivative is not None else None,
        "features": features,
        "checks": checks,
        "passed": all(checks[name] for name in simulation["checks"]),
    }

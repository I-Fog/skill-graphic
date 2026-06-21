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


def _sign_at(expr: sp.Expr, x: sp.Symbol, value: sp.Expr, step: sp.Expr) -> tuple[int, int]:
    left = sp.N(expr.subs(x, value - step))
    right = sp.N(expr.subs(x, value + step))
    return int(sp.sign(left)), int(sp.sign(right))


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
        step = sp.Rational(1, 100)
        fx = sp.simplify(function.subs(x, px))
        if "y" in point and not _is_zero(fx - sp.sympify(point["y"], locals=locals_map)):
            return False
        kind = point["kind"]
        if kind == "root" and not _is_zero(fx):
            return False
        if kind == "extremum":
            if not _is_zero(derivative.subs(x, px)):
                return False
            left_sign, right_sign = _sign_at(derivative, x, px, step)
            if left_sign == 0 or right_sign == 0 or left_sign == right_sign:
                return False
        if kind == "inflection":
            if not _is_zero(second_derivative.subs(x, px)):
                return False
            left_sign, right_sign = _sign_at(second_derivative, x, px, step)
            if left_sign == 0 or right_sign == 0 or left_sign == right_sign:
                return False
    return True


def _intervals_match(
    features: dict[str, Any],
    x: sp.Symbol,
    function: sp.Expr,
    derivative: sp.Expr,
    locals_map: dict[str, Any],
) -> bool:
    for interval in features.get("highlighted_intervals", []):
        start = sp.sympify(interval["start"], locals=locals_map)
        end = sp.sympify(interval["end"], locals=locals_map)
        if not bool(sp.N(start) < sp.N(end)):
            return False
        samples = [
            start + (end - start) * sp.Rational(index, 6)
            for index in range(1, 6)
        ]
        kind = interval["kind"]
        if kind == "increasing" and not all(sp.N(derivative.subs(x, sample)) > 0 for sample in samples):
            return False
        if kind == "decreasing" and not all(sp.N(derivative.subs(x, sample)) < 0 for sample in samples):
            return False
        if kind == "positive" and not all(sp.N(function.subs(x, sample)) > 0 for sample in samples):
            return False
        if kind == "negative" and not all(sp.N(function.subs(x, sample)) < 0 for sample in samples):
            return False
    return True


def _real_roots_in_interval(expr: sp.Expr, x: sp.Symbol, start: sp.Expr, end: sp.Expr) -> set[str]:
    roots: set[str] = set()
    for root in sp.solve(expr, x):
        numeric = sp.N(root)
        if numeric.is_real is False:
            continue
        try:
            if bool(sp.N(start) < numeric < sp.N(end)):
                roots.add(stringify(root))
        except TypeError:
            continue
    return roots


def _asymptotes_match(
    features: dict[str, Any],
    x: sp.Symbol,
    function: sp.Expr,
    locals_map: dict[str, Any],
    domain_start: sp.Expr,
    domain_end: sp.Expr,
) -> bool:
    numerator, denominator = sp.fraction(sp.cancel(function))
    del numerator
    declared = {
        stringify(sp.sympify(item["x"], locals=locals_map))
        for item in features.get("vertical_asymptotes", [])
    }
    denominator_roots = _real_roots_in_interval(denominator, x, domain_start, domain_end)
    if not denominator_roots.issubset(declared):
        return False
    for item in features.get("vertical_asymptotes", []):
        value = sp.sympify(item["x"], locals=locals_map)
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
    domain_start: sp.Expr,
    domain_end: sp.Expr,
) -> bool:
    numerator, denominator = sp.fraction(function)
    del numerator
    singular_roots = _real_roots_in_interval(denominator, x, domain_start, domain_end)
    declared = {
        stringify(sp.sympify(item["x"], locals=locals_map))
        for item in features.get("discontinuities", [])
    }
    asymptotes = {
        stringify(sp.sympify(item["x"], locals=locals_map))
        for item in features.get("vertical_asymptotes", [])
    }
    if not singular_roots.issubset(declared | asymptotes):
        return False
    for item in features.get("discontinuities", []):
        value = sp.sympify(item["x"], locals=locals_map)
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
        "declared_intervals_match_function": _intervals_match(
            features,
            variable,
            function_for_checks,
            derivative_for_checks,
            locals_map,
        ),
        "declared_asymptotes_match_function": _asymptotes_match(
            features,
            variable,
            function_for_checks,
            locals_map,
            domain_start,
            domain_end,
        ),
        "declared_discontinuities_match_function": _discontinuities_match(
            features,
            variable,
            function_for_checks,
            locals_map,
            domain_start,
            domain_end,
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

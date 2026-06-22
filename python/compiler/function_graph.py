from __future__ import annotations

from typing import Any

import sympy as sp

try:
    from validator.sympy_utils import stringify
except ImportError:
    import sys
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT / "python" / "validator"))
    from sympy_utils import stringify  # type: ignore


SAMPLE_COUNT = 97
TANGENT_HALF_WIDTH = 0.55


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


def _parse_parameters(simulation: dict[str, Any]) -> tuple[dict[str, sp.Symbol], dict[sp.Symbol, sp.Expr]]:
    symbols: dict[str, sp.Symbol] = {}
    numeric_values: dict[sp.Symbol, sp.Expr] = {}
    for name, payload in simulation.get("parameters", {}).items():
        symbol = sp.symbols(name, real=True)
        symbols[name] = symbol
        numeric_values[symbol] = sp.sympify(payload["value"])
    return symbols, numeric_values


def _float(expr: sp.Expr) -> float:
    return round(float(sp.N(expr)), 10)


def _finite_float(expr: sp.Expr) -> float | None:
    try:
        value = float(sp.N(expr))
    except (TypeError, ValueError, OverflowError):
        return None
    if value != value or value in (float("inf"), float("-inf")):
        return None
    if abs(value) > 1e8:
        return None
    return round(value, 10)


def _sample_curve(expr: sp.Expr, variable: sp.Symbol, start: sp.Expr, end: sp.Expr) -> list[list[dict[str, float]]]:
    segments: list[list[dict[str, float]]] = []
    current: list[dict[str, float]] = []
    for index in range(SAMPLE_COUNT):
        ratio = sp.Rational(index, SAMPLE_COUNT - 1)
        x_value = start + (end - start) * ratio
        y_value = _finite_float(expr.subs(variable, x_value))
        if y_value is None:
            if current:
                segments.append(current)
                current = []
            continue
        current.append({"x": _float(x_value), "y": y_value})
    if current:
        segments.append(current)
    return segments


def _flatten_y_values(curves: list[dict[str, Any]], points: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for curve in curves:
        for segment in curve["segments"]:
            values.extend(point["y"] for point in segment)
    values.extend(point["y"] for point in points if "y" in point)
    return values


def _viewport(domain_start: float, domain_end: float, y_values: list[float]) -> dict[str, float]:
    y_min = min(y_values) if y_values else -1.0
    y_max = max(y_values) if y_values else 1.0
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0
    y_pad = (y_max - y_min) * 0.12
    x_pad = (domain_end - domain_start) * 0.06
    return {
        "x_min": round(domain_start - x_pad, 10),
        "x_max": round(domain_end + x_pad, 10),
        "y_min": round(y_min - y_pad, 10),
        "y_max": round(y_max + y_pad, 10),
    }


def _viewport_for_curve(curve: dict[str, Any], domain_start: float, domain_end: float) -> dict[str, float]:
    return _viewport(domain_start, domain_end, _flatten_y_values([curve], []))


def _compile_points(
    features: dict[str, Any],
    variable: sp.Symbol,
    function: sp.Expr,
    locals_map: dict[str, Any],
    parameter_values: dict[sp.Symbol, sp.Expr],
) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for point in features.get("special_points", []):
        x_expr = sp.sympify(point["x"], locals=locals_map).subs(parameter_values)
        y_expr = sp.sympify(point.get("y", function.subs(variable, x_expr)), locals=locals_map).subs(parameter_values)
        points.append(
            {
                "id": point["id"],
                "kind": point["kind"],
                "label": point.get("label", point["kind"]),
                "x": _float(x_expr),
                "y": _float(y_expr),
                "x_expr": stringify(x_expr),
                "y_expr": stringify(y_expr),
            }
        )
    return points


def _compile_intervals(
    features: dict[str, Any],
    locals_map: dict[str, Any],
    parameter_values: dict[sp.Symbol, sp.Expr],
) -> list[dict[str, Any]]:
    intervals: list[dict[str, Any]] = []
    for interval in features.get("highlighted_intervals", []):
        start = sp.sympify(interval["start"], locals=locals_map).subs(parameter_values)
        end = sp.sympify(interval["end"], locals=locals_map).subs(parameter_values)
        intervals.append(
            {
                "id": interval["id"],
                "kind": interval["kind"],
                "label": interval.get("label", interval["kind"]),
                "start": _float(start),
                "end": _float(end),
                "start_expr": stringify(start),
                "end_expr": stringify(end),
            }
        )
    return intervals


def _compile_tangents(
    simulation: dict[str, Any],
    points: list[dict[str, Any]],
    variable: sp.Symbol,
    derivative: sp.Expr,
) -> list[dict[str, Any]]:
    points_by_id = {point["id"]: point for point in points}
    tangents: list[dict[str, Any]] = []
    seen: set[str] = set()
    for scene in simulation.get("scenes", []):
        if scene.get("action") != "show_tangent":
            continue
        point_id = scene.get("args", {}).get("point_id")
        if not point_id or point_id in seen:
            continue
        point = points_by_id[point_id]
        slope = _finite_float(derivative.subs(variable, point["x"]))
        if slope is None:
            continue
        x1 = round(point["x"] - TANGENT_HALF_WIDTH, 10)
        x2 = round(point["x"] + TANGENT_HALF_WIDTH, 10)
        y1 = round(point["y"] + slope * (x1 - point["x"]), 10)
        y2 = round(point["y"] + slope * (x2 - point["x"]), 10)
        tangents.append(
            {
                "id": f"tangent-{point_id}",
                "point_id": point_id,
                "slope": slope,
                "line": [{"x": x1, "y": y1}, {"x": x2, "y": y2}],
            }
        )
        seen.add(point_id)
    return tangents


def _camera_policy_for(scene: dict[str, Any]) -> dict[str, Any]:
    action = scene["action"]
    if action == "trace_point":
        return {"mode": "trace", "zoom": 0.98, "tilt": 0.28, "focus": "function"}
    if action == "show_tangent":
        return {
            "mode": "targets",
            "zoom": 0.98,
            "tilt": 0.28,
            "targets": [scene.get("args", {}).get("point_id")] if scene.get("args", {}).get("point_id") else scene.get("targets", []),
        }
    if action in {"show_extrema", "show_inflection", "show_asymptote", "show_discontinuity"}:
        return {"mode": "targets", "zoom": 0.98, "tilt": 0.28, "targets": scene.get("targets", [])}
    if action == "show_derivative_graph":
        return {"mode": "curve", "zoom": 0.9, "tilt": 0.42, "curve_id": "derivative"}
    if action == "show_antiderivative_graph":
        return {"mode": "curve", "zoom": 0.9, "tilt": 0.42, "curve_id": "antiderivative"}
    return {"mode": "overview", "zoom": 1.0, "tilt": 0.18}


def _compile_scenes(simulation: dict[str, Any]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    cursor = 0
    for scene in simulation["scenes"]:
        duration = int(scene.get("duration_ms", 900))
        timeline.append(
            {
                "id": scene["id"],
                "goal": scene["goal"],
                "action": scene["action"],
                "start_ms": cursor,
                "duration_ms": duration,
                "end_ms": cursor + duration,
                "caption": scene.get("caption", ""),
                "formula": scene.get("formula", ""),
                "targets": scene.get("targets", []),
                "args": scene.get("args", {}),
                "camera": _camera_policy_for(scene),
            }
        )
        cursor += duration
    return timeline


def compile_function_graph_render_model(simulation: dict[str, Any], math_result: dict[str, Any]) -> dict[str, Any]:
    if simulation.get("type") != "function_graph":
        raise ValueError("compile_function_graph_render_model requires a function_graph simulation.")
    if not math_result.get("passed"):
        raise ValueError("Cannot compile a render model from failed math validation.")

    variable = sp.symbols(simulation["math"]["variable"], real=True)
    parameter_symbols, parameter_values = _parse_parameters(simulation)
    locals_map = _locals(variable, parameter_symbols)
    math = simulation["math"]
    domain_start = sp.sympify(math["domain"][0], locals=locals_map).subs(parameter_values)
    domain_end = sp.sympify(math["domain"][1], locals=locals_map).subs(parameter_values)
    function = sp.sympify(math["function"], locals=locals_map).subs(parameter_values)
    derivative = sp.diff(function, variable)
    antiderivative = (
        sp.sympify(math["antiderivative"], locals=locals_map).subs(parameter_values)
        if "antiderivative" in math
        else None
    )

    curves = [
        {
            "id": "function",
            "role": "primary",
            "label": "f(x)",
            "expression": math_result["function"],
            "segments": _sample_curve(function, variable, domain_start, domain_end),
        },
        {
            "id": "derivative",
            "role": "support",
            "label": "f'(x)",
            "expression": math_result["derivative"],
            "segments": _sample_curve(derivative, variable, domain_start, domain_end),
        },
    ]
    if antiderivative is not None:
        curves.append(
            {
                "id": "antiderivative",
                "role": "support",
                "label": "F(x)",
                "expression": math_result["antiderivative"],
                "segments": _sample_curve(antiderivative, variable, domain_start, domain_end),
            }
        )

    features = simulation.get("features", {})
    points = _compile_points(features, variable, function, locals_map, parameter_values)
    intervals = _compile_intervals(features, locals_map, parameter_values)
    tangents = _compile_tangents(simulation, points, variable, derivative)
    numeric_domain_start = _float(domain_start)
    numeric_domain_end = _float(domain_end)
    primary_viewport = _viewport(numeric_domain_start, numeric_domain_end, _flatten_y_values([curves[0]], points))
    full_viewport = _viewport(numeric_domain_start, numeric_domain_end, _flatten_y_values(curves, points))
    curve_viewports = {
        curve["id"]: _viewport_for_curve(curve, numeric_domain_start, numeric_domain_end)
        for curve in curves
    }
    scenes = _compile_scenes(simulation)

    return {
        "schema_version": 1,
        "simulation_id": simulation["id"],
        "type": "function_graph_render_model",
        "title": simulation["title"],
        "language": simulation["language"],
        "variable": simulation["math"]["variable"],
        "domain": {"start": numeric_domain_start, "end": numeric_domain_end},
        "viewport": primary_viewport,
        "full_viewport": full_viewport,
        "curve_viewports": curve_viewports,
        "curves": curves,
        "features": {
            "points": points,
            "intervals": intervals,
            "vertical_asymptotes": features.get("vertical_asymptotes", []),
            "discontinuities": features.get("discontinuities", []),
            "tangents": tangents,
        },
        "timeline": {
            "duration_ms": scenes[-1]["end_ms"] if scenes else 0,
            "scenes": scenes,
            "easing": "easeInOutCubic",
        },
        "checks": math_result["checks"],
        "contract_hash": math_result["contract_hash"],
    }

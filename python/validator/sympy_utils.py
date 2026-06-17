from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import sympy as sp


@dataclass(frozen=True)
class ParsedSurfaceInput:
    variable: sp.Symbol
    parameters: dict[str, sp.Symbol]
    function: sp.Expr
    domain_start: sp.Expr
    domain_end: sp.Expr


def parse_surface_input(simulation: dict[str, Any]) -> ParsedSurfaceInput:
    variable_name = simulation["math"]["variable"]
    variable = sp.symbols(variable_name, nonnegative=True)

    parameter_symbols = {
        name: sp.symbols(name, positive=True)
        for name in simulation.get("parameters", {}).keys()
    }

    locals_map: dict[str, Any] = {
        variable_name: variable,
        "sqrt": sp.sqrt,
        "sin": sp.sin,
        "cos": sp.cos,
        "pi": sp.pi
    }
    locals_map.update(parameter_symbols)

    function = sp.sympify(simulation["math"]["function"], locals=locals_map)
    start_raw, end_raw = simulation["math"]["domain"]
    domain_start = sp.sympify(start_raw, locals=locals_map)
    domain_end = sp.sympify(end_raw, locals=locals_map)

    return ParsedSurfaceInput(
        variable=variable,
        parameters=parameter_symbols,
        function=function,
        domain_start=domain_start,
        domain_end=domain_end,
    )


def stringify(expr: sp.Expr) -> str:
    return str(sp.simplify(expr))

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .contract import contract_hash, validate_contract_semantics
    from .function_graph import validate_function_graph
    from .indefinite_integral import validate_indefinite_integral
    from .surface_revolution import validate_surface_of_revolution
except ImportError:
    from contract import contract_hash, validate_contract_semantics
    from function_graph import validate_function_graph
    from indefinite_integral import validate_indefinite_integral
    from surface_revolution import validate_surface_of_revolution


def validate_math(simulation: dict) -> dict:
    validate_contract_semantics(simulation)
    if simulation.get("type") == "function_graph":
        result = validate_function_graph(simulation)
    elif simulation.get("type") == "surface_of_revolution":
        result = validate_surface_of_revolution(simulation)
    elif simulation.get("type") == "indefinite_integral":
        result = validate_indefinite_integral(simulation)
    else:
        raise ValueError(f"Unsupported simulation type: {simulation.get('type')}")
    result["contract_hash"] = contract_hash(simulation)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate simulation math with SymPy.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    simulation = json.loads(args.input.read_text(encoding="utf-8"))
    result = validate_math(simulation)
    payload = json.dumps(result, ensure_ascii=True, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"math validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

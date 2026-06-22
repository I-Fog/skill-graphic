from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "python" / "validator"))

from compiler.function_graph import compile_function_graph_render_model  # noqa: E402
from contract import contract_hash  # noqa: E402
from validate_math import validate_math  # noqa: E402

SCHEMA = ROOT / "schemas" / "simulation.schema.json"


def render_template(template: str, values: dict[str, str]) -> str:
    output = template
    for key, value in values.items():
        output = output.replace("{{ " + key + " }}", value)
    return output


def check_summary_for(math_result: dict) -> str:
    passed = [name for name, ok in math_result["checks"].items() if ok]
    return "Validated: " + ", ".join(passed)


def build_surface_revolution_html(simulation: dict, math_result: dict) -> str:
    template = (ROOT / "assets" / "templates" / "surface_revolution.html").read_text(encoding="utf-8")
    parameter = simulation["parameters"]["a"]

    check_summary = check_summary_for(math_result)

    render_payload = dict(simulation)
    render_payload["render"] = {
        "initialFormula": f"f(x) = {simulation['math']['function']}",
        "checkSummary": check_summary,
    }

    values = {
        "language": html.escape(simulation["language"]),
        "title": html.escape(simulation["title"]),
        "simulation_id": html.escape(simulation["id"]),
        "first_caption": html.escape(simulation["scenes"][0].get("caption", "")),
        "initial_formula": html.escape(f"f(x) = {simulation['math']['function']}"),
        "check_summary": html.escape(check_summary),
        "a_value": str(parameter["value"]),
        "a_min": str(parameter.get("min", 0.5)),
        "a_max": str(parameter.get("max", 5)),
        "a_step": str(parameter.get("step", 0.1)),
        "simulation_json": json.dumps(render_payload, ensure_ascii=True).replace("</", "<\\/"),
    }
    return render_template(template, values)


def build_indefinite_integral_html(simulation: dict, math_result: dict) -> str:
    template = (ROOT / "assets" / "templates" / "indefinite_integral.html").read_text(encoding="utf-8")

    check_summary = check_summary_for(math_result)

    render_payload = dict(simulation)
    render_payload["render"] = {
        "initialFormula": simulation["scenes"][0].get("formula", simulation["math"]["integrand"]),
        "checkSummary": check_summary,
    }

    values = {
        "language": html.escape(simulation["language"]),
        "title": html.escape(simulation["title"]),
        "simulation_id": html.escape(simulation["id"]),
        "first_goal": html.escape(simulation["scenes"][0].get("goal", "")),
        "first_caption": html.escape(simulation["scenes"][0].get("caption", "")),
        "initial_formula": html.escape(simulation["scenes"][0].get("formula", simulation["math"]["integrand"])),
        "check_summary": html.escape(check_summary),
        "simulation_json": json.dumps(render_payload, ensure_ascii=True).replace("</", "<\\/"),
    }
    return render_template(template, values)


def build_function_graph_html(simulation: dict, math_result: dict, output: Path | None = None) -> str:
    template = (ROOT / "assets" / "templates" / "function_graph.html").read_text(encoding="utf-8")

    check_summary = check_summary_for(math_result)
    render_model = compile_function_graph_render_model(simulation, math_result)
    if output is not None:
        render_output = output.with_suffix(".render.json")
        render_output.parent.mkdir(parents=True, exist_ok=True)
        render_output.write_text(json.dumps(render_model, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    render_payload = dict(simulation)
    render_payload["renderModel"] = render_model
    render_payload["render"] = {
        "initialFormula": simulation["scenes"][0].get("formula", simulation["math"]["function"]),
        "checkSummary": check_summary,
    }

    values = {
        "language": html.escape(simulation["language"]),
        "title": html.escape(simulation["title"]),
        "simulation_id": html.escape(simulation["id"]),
        "first_goal": html.escape(simulation["scenes"][0].get("goal", "")),
        "first_caption": html.escape(simulation["scenes"][0].get("caption", "")),
        "initial_formula": html.escape(simulation["scenes"][0].get("formula", simulation["math"]["function"])),
        "simulation_json": json.dumps(render_payload, ensure_ascii=True).replace("</", "<\\/"),
    }
    return render_template(template, values)


def load_schema() -> dict:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


def validate_or_load_math_result(simulation: dict, path: Path | None) -> dict:
    jsonschema.validate(simulation, load_schema())
    expected_hash = contract_hash(simulation)
    if path:
        cached_result = json.loads(path.read_text(encoding="utf-8"))
        if cached_result.get("id") != simulation.get("id"):
            raise ValueError("Math result id does not match simulation id.")
        if cached_result.get("type") != simulation.get("type"):
            raise ValueError("Math result type does not match simulation type.")
        if cached_result.get("contract_hash") != expected_hash:
            raise ValueError("Math result contract_hash is missing or stale.")
        if not cached_result.get("passed"):
            raise ValueError("Math result did not pass validation.")

    math_result = validate_math(simulation)
    if not math_result.get("passed"):
        raise ValueError("Math validation did not pass.")
    return math_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate interactive simulation HTML.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--math-result", type=Path)
    args = parser.parse_args()

    simulation = json.loads(args.input.read_text(encoding="utf-8"))
    math_result = validate_or_load_math_result(simulation, args.math_result)
    if simulation.get("type") == "surface_of_revolution":
        html_output = build_surface_revolution_html(simulation, math_result)
    elif simulation.get("type") == "indefinite_integral":
        html_output = build_indefinite_integral_html(simulation, math_result)
    elif simulation.get("type") == "function_graph":
        html_output = build_function_graph_html(simulation, math_result, args.output)
    else:
        print(f"Unsupported simulation type: {simulation.get('type')}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_output, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

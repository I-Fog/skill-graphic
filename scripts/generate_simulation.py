from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render_template(template: str, values: dict[str, str]) -> str:
    output = template
    for key, value in values.items():
        output = output.replace("{{ " + key + " }}", value)
    return output


def build_surface_revolution_html(simulation: dict, math_result: dict | None) -> str:
    template = (ROOT / "assets" / "templates" / "surface_revolution.html").read_text(encoding="utf-8")
    parameter = simulation["parameters"]["a"]

    check_summary = "Checks pending."
    if math_result:
        passed = [name for name, ok in math_result["checks"].items() if ok]
        check_summary = "Validated: " + ", ".join(passed)

    render_payload = dict(simulation)
    render_payload["render"] = {
        "initialFormula": "f(x) = x sqrt(x / a)",
        "checkSummary": check_summary,
    }

    values = {
        "language": html.escape(simulation["language"]),
        "title": html.escape(simulation["title"]),
        "simulation_id": html.escape(simulation["id"]),
        "first_caption": html.escape(simulation["scenes"][0].get("caption", "")),
        "initial_formula": "f(x) = x sqrt(x / a)",
        "check_summary": html.escape(check_summary),
        "a_value": str(parameter["value"]),
        "a_min": str(parameter.get("min", 0.5)),
        "a_max": str(parameter.get("max", 5)),
        "a_step": str(parameter.get("step", 0.1)),
        "simulation_json": json.dumps(render_payload, ensure_ascii=True).replace("</", "<\\/"),
    }
    return render_template(template, values)


def load_math_result(path: Path | None) -> dict | None:
    if not path:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate interactive simulation HTML.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--math-result", type=Path)
    args = parser.parse_args()

    simulation = json.loads(args.input.read_text(encoding="utf-8"))
    if simulation.get("type") != "surface_of_revolution":
        print(f"Unsupported simulation type: {simulation.get('type')}", file=sys.stderr)
        return 1

    html_output = build_surface_revolution_html(simulation, load_math_result(args.math_result))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_output, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

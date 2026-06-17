from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "simulation.schema.json"
EXAMPLE = ROOT / "examples" / "surface-revolution" / "input.json"
MATH_OUTPUT = ROOT / "dist" / "surface-revolution.math.json"
HTML_OUTPUT = ROOT / "dist" / "surface-revolution.html"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path} is missing expected fragments: {missing}")


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(example, schema)

    run([sys.executable, "python/validator/validate_math.py", str(EXAMPLE), "--output", str(MATH_OUTPUT)])
    math_result = json.loads(MATH_OUTPUT.read_text(encoding="utf-8"))
    if not math_result.get("passed"):
        raise AssertionError("Math validation did not pass.")

    run([
        sys.executable,
        "scripts/generate_simulation.py",
        str(EXAMPLE),
        str(HTML_OUTPUT),
        "--math-result",
        str(MATH_OUTPUT),
    ])

    assert_contains(
        HTML_OUTPUT,
        [
            'data-simulation-id="surface-revolution-canonical"',
            '<svg id="plot"',
            'id="three-root"',
            'rotate_curve_into_surface',
            'Validated:',
            '{"id": "surface-revolution-canonical"',
        ],
    )
    assert "&quot;" not in HTML_OUTPUT.read_text(encoding="utf-8").split('id="simulation-data"', 1)[1].split("</script>", 1)[0]

    print(f"Smoke tests passed: {HTML_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "simulation.schema.json"
SURFACE_EXAMPLE = ROOT / "examples" / "surface-revolution" / "input.json"
SURFACE_MATH_OUTPUT = ROOT / "dist" / "surface-revolution.math.json"
SURFACE_HTML_OUTPUT = ROOT / "dist" / "surface-revolution.html"
FUNCTION_EXAMPLE = ROOT / "examples" / "function-graph-cubic" / "input.json"
FUNCTION_MATH_OUTPUT = ROOT / "dist" / "function-graph-cubic.math.json"
INTEGRAL_EXAMPLE = ROOT / "examples" / "indefinite-integral-tan-sin" / "input.json"
INTEGRAL_MATH_OUTPUT = ROOT / "dist" / "indefinite-integral-tan-sin.math.json"
INTEGRAL_HTML_OUTPUT = ROOT / "dist" / "indefinite-integral-tan-sin.html"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f"{path} is missing expected fragments: {missing}")


def generate_checked(example_path: Path, math_output: Path, html_output: Path, schema: dict) -> dict:
    example = json.loads(example_path.read_text(encoding="utf-8"))
    jsonschema.validate(example, schema)

    run([sys.executable, "python/validator/validate_math.py", str(example_path), "--output", str(math_output)])
    math_result = json.loads(math_output.read_text(encoding="utf-8"))
    if not math_result.get("passed"):
        raise AssertionError(f"Math validation did not pass for {example_path}.")

    run([
        sys.executable,
        "scripts/generate_simulation.py",
        str(example_path),
        str(html_output),
        "--math-result",
        str(math_output),
    ])
    return math_result


def validate_checked(example_path: Path, math_output: Path, schema: dict) -> dict:
    example = json.loads(example_path.read_text(encoding="utf-8"))
    jsonschema.validate(example, schema)

    run([sys.executable, "python/validator/validate_math.py", str(example_path), "--output", str(math_output)])
    math_result = json.loads(math_output.read_text(encoding="utf-8"))
    if not math_result.get("passed"):
        raise AssertionError(f"Math validation did not pass for {example_path}.")
    return math_result


def check_surface_html() -> None:
    assert_contains(
        SURFACE_HTML_OUTPUT,
        [
            'data-simulation-id="surface-revolution-canonical"',
            '<svg id="plot"',
            'id="surface-wireframe"',
            'id="timeline"',
            'id="formula-panel"',
            'rotate_curve_into_surface',
            'Validated:',
            '{"id": "surface-revolution-canonical"',
            'function easeInOut(t)',
            'function setTimelineValue(value)',
            'function initialTimelineFromUrl()',
            'function projectSurfacePoint(x, y, z, a, frontView)',
            'const surfaceSceneProgress = sceneIndex === 4 ? easedProgress',
            'const cameraSceneProgress = sceneIndex === 4 ? easedProgress',
        ],
    )
    html_text = SURFACE_HTML_OUTPUT.read_text(encoding="utf-8")
    if 'id="three-root"' in html_text:
        raise AssertionError("Generated HTML must use one visual stage, not a separate 3D panel.")
    if "three.module" in html_text or "from 'three'" in html_text or 'from "three"' in html_text:
        raise AssertionError("Generated HTML must not import a separate Three.js renderer for the canonical fixture.")
    if 'addEventListener("resize", resize)' in html_text:
        raise AssertionError("Generated HTML references a removed resize handler.")
    if 'id="progress"' in html_text:
        raise AssertionError("Generated HTML must expose the timeline as a scrubber, not a passive progress span.")
    if '<section class="detail">' in html_text or 'id="checks"' in html_text:
        raise AssertionError("Generated HTML must not include the removed lower formula/checks band.")
    assert "&quot;" not in SURFACE_HTML_OUTPUT.read_text(encoding="utf-8").split('id="simulation-data"', 1)[1].split("</script>", 1)[0]


def check_integral_html() -> None:
    assert_contains(
        INTEGRAL_HTML_OUTPUT,
        [
            'data-simulation-id="indefinite-integral-tan-sin"',
            '<svg id="plot"',
            'id="integrand"',
            'id="area"',
            'id="primitive"',
            'id="family"',
            'id="timeline"',
            'draw_integrand_graph',
            'sweep_signed_area',
            'draw_primitive_curve',
            'show_primitive_family',
            'function areaForCursor(xCursor)',
            'function initialTimelineFromUrl()',
            'F(x)=',
        ],
    )
    html_text = INTEGRAL_HTML_OUTPUT.read_text(encoding="utf-8")
    if 'id="three-root"' in html_text:
        raise AssertionError("Integral HTML must use its own Cartesian SVG stage.")
    if "<canvas" in html_text:
        raise AssertionError("Integral MVP should render the graph with SVG, not canvas.")
    assert "&quot;" not in html_text.split('id="simulation-data"', 1)[1].split("</script>", 1)[0]


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)

    generate_checked(SURFACE_EXAMPLE, SURFACE_MATH_OUTPUT, SURFACE_HTML_OUTPUT, schema)
    check_surface_html()

    validate_checked(FUNCTION_EXAMPLE, FUNCTION_MATH_OUTPUT, schema)

    generate_checked(INTEGRAL_EXAMPLE, INTEGRAL_MATH_OUTPUT, INTEGRAL_HTML_OUTPUT, schema)
    check_integral_html()

    print(f"Smoke tests passed: {SURFACE_HTML_OUTPUT}")
    print(f"Smoke tests passed: {FUNCTION_MATH_OUTPUT}")
    print(f"Smoke tests passed: {INTEGRAL_HTML_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

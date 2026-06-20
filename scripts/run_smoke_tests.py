from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python" / "validator"))

from validate_math import validate_math  # noqa: E402

SCHEMA = ROOT / "schemas" / "simulation.schema.json"
SURFACE_EXAMPLE = ROOT / "examples" / "surface-revolution" / "input.json"
SURFACE_MATH_OUTPUT = ROOT / "dist" / "surface-revolution.math.json"
SURFACE_HTML_OUTPUT = ROOT / "dist" / "surface-revolution.html"
FUNCTION_EXAMPLE = ROOT / "examples" / "function-graph-cubic" / "input.json"
FUNCTION_MATH_OUTPUT = ROOT / "dist" / "function-graph-cubic.math.json"
FUNCTION_EXPECTED = ROOT / "examples" / "function-graph-cubic" / "expected-math.json"
INTEGRAL_EXAMPLE = ROOT / "examples" / "indefinite-integral-tan-sin" / "input.json"
INTEGRAL_MATH_OUTPUT = ROOT / "dist" / "indefinite-integral-tan-sin.math.json"
INTEGRAL_HTML_OUTPUT = ROOT / "dist" / "indefinite-integral-tan-sin.html"
INTEGRAL_EXPECTED = ROOT / "examples" / "indefinite-integral-tan-sin" / "expected-math.json"
SURFACE_EXPECTED = ROOT / "examples" / "surface-revolution" / "expected-math.json"
TMP_OUTPUT = ROOT / "dist" / "_tmp-smoke-output.html"
TMP_MATH_OUTPUT = ROOT / "dist" / "_tmp-stale-math.json"


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


def assert_expected_math(math_result: dict, expected_path: Path) -> None:
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    if "passed" in expected and math_result.get("passed") != expected.get("passed"):
        raise AssertionError(f"{expected_path} expected passed={expected.get('passed')}.")
    for name, expected_value in expected.get("checks", {}).items():
        actual = math_result.get("checks", {}).get(name)
        if actual != expected_value:
            raise AssertionError(f"{expected_path} expected {name}={expected_value}, got {actual}.")


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


def assert_validation_fails(example: dict, label: str) -> None:
    try:
        result = validate_math(example)
    except Exception:
        return
    if result.get("passed"):
        raise AssertionError(f"Negative validation unexpectedly passed: {label}")


def check_negative_validation_cases(schema: dict) -> None:
    surface = json.loads(SURFACE_EXAMPLE.read_text(encoding="utf-8"))
    surface["math"]["domain"] = ["a", "0"]
    jsonschema.validate(surface, schema)
    assert_validation_fails(surface, "surface inverted domain")

    cubic = json.loads(FUNCTION_EXAMPLE.read_text(encoding="utf-8"))
    cubic["math"]["function"] = "x**3"
    cubic["math"]["derivative"] = "3*x**2"
    cubic["math"]["antiderivative"] = "x**4/4"
    cubic["features"]["special_points"] = [{"id": "false-extremum", "kind": "extremum", "x": "0", "y": "0"}]
    cubic["features"]["highlighted_intervals"] = []
    jsonschema.validate(cubic, schema)
    assert_validation_fails(cubic, "x^3 false extremum")

    quartic = json.loads(FUNCTION_EXAMPLE.read_text(encoding="utf-8"))
    quartic["math"]["function"] = "x**4"
    quartic["math"]["derivative"] = "4*x**3"
    quartic["math"]["antiderivative"] = "x**5/5"
    quartic["features"]["special_points"] = [{"id": "false-inflection", "kind": "inflection", "x": "0", "y": "0"}]
    quartic["features"]["highlighted_intervals"] = []
    jsonschema.validate(quartic, schema)
    assert_validation_fails(quartic, "x^4 false inflection")

    rational = json.loads(FUNCTION_EXAMPLE.read_text(encoding="utf-8"))
    rational["math"]["function"] = "1/x"
    rational["math"]["derivative"] = "-1/x**2"
    rational["math"]["antiderivative"] = "log(x)"
    rational["features"]["special_points"] = []
    rational["features"]["highlighted_intervals"] = []
    rational["features"]["vertical_asymptotes"] = []
    rational["features"]["discontinuities"] = []
    jsonschema.validate(rational, schema)
    assert_validation_fails(rational, "omitted rational asymptote")


def check_generator_validation_gate() -> None:
    if TMP_OUTPUT.exists():
        TMP_OUTPUT.unlink()
    run([
        sys.executable,
        "scripts/generate_simulation.py",
        str(SURFACE_EXAMPLE),
        str(TMP_OUTPUT),
    ])
    if not TMP_OUTPUT.exists():
        raise AssertionError("Generator did not produce HTML when running its own validation.")
    TMP_OUTPUT.unlink()

    stale_result = deepcopy(json.loads(SURFACE_MATH_OUTPUT.read_text(encoding="utf-8")))
    stale_result["contract_hash"] = "stale"
    TMP_MATH_OUTPUT.write_text(json.dumps(stale_result), encoding="utf-8")
    failed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_simulation.py",
            str(SURFACE_EXAMPLE),
            str(TMP_OUTPUT),
            "--math-result",
            str(TMP_MATH_OUTPUT),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    TMP_MATH_OUTPUT.unlink(missing_ok=True)
    TMP_OUTPUT.unlink(missing_ok=True)
    if failed.returncode == 0:
        raise AssertionError("Generator accepted a stale math result.")


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)

    surface_result = generate_checked(SURFACE_EXAMPLE, SURFACE_MATH_OUTPUT, SURFACE_HTML_OUTPUT, schema)
    assert_expected_math(surface_result, SURFACE_EXPECTED)
    check_surface_html()

    function_result = validate_checked(FUNCTION_EXAMPLE, FUNCTION_MATH_OUTPUT, schema)
    assert_expected_math(function_result, FUNCTION_EXPECTED)

    integral_result = generate_checked(INTEGRAL_EXAMPLE, INTEGRAL_MATH_OUTPUT, INTEGRAL_HTML_OUTPUT, schema)
    assert_expected_math(integral_result, INTEGRAL_EXPECTED)
    check_integral_html()
    check_negative_validation_cases(schema)
    check_generator_validation_gate()

    print(f"Smoke tests passed: {SURFACE_HTML_OUTPUT}")
    print(f"Smoke tests passed: {FUNCTION_MATH_OUTPUT}")
    print(f"Smoke tests passed: {INTEGRAL_HTML_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

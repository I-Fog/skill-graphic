from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUNDS_ROOT = ROOT / "docs" / "review" / "pro-rounds"


def run(command: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def command_text(command: list[str]) -> str:
    completed = run(command)
    output = (completed.stdout + completed.stderr).strip()
    if not output:
        output = "(no output)"
    return f"$ {' '.join(command)}\n{output}"


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def safe_read(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        return f"(missing: {relative_path})"
    return read_file(path)


def current_round_id() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def round_path(round_id: str) -> Path:
    return ROUNDS_ROOT / round_id


def build_prompt(round_id: str, focus: str) -> str:
    repo_url = "https://github.com/I-Fog/skill-graphic"
    status = command_text(["git", "status", "--short"])
    branch = command_text(["git", "branch", "--show-current"])
    head = command_text(["git", "rev-parse", "HEAD"])
    latest = command_text(["git", "show", "--stat", "--oneline", "--decorate", "-1"])
    diff = command_text(["git", "diff", "--stat"])

    return f"""# Solicitud de revisión para ChatGPT Pro

Repositorio: {repo_url}
Rama esperada: `codex/skill-graphic-mvp`
Ronda: `{round_id}`

## Rol

Actúa como validador técnico y planificador externo del proyecto `skill-graphic`.
No ejecutes tests: revisa estáticamente el repo y el contexto incluido. Tu salida debe ayudar a Codex a decidir el siguiente cambio.

## Foco de esta ronda

{focus}

## Preguntas obligatorias

1. ¿El estado actual permite avanzar al siguiente incremento o hay P0 antes?
2. ¿Qué cambios concretos debe aplicar Codex en la siguiente iteración?
3. ¿Qué evidencias o tests faltan para creer los cambios?
4. ¿Hay contradicciones entre contrato, docs, fixtures, validadores y generador?

## Formato de respuesta

Devuelve:

- `Dictamen`: aprobado, aprobado con cambios, o cambios solicitados.
- `P0`: bloqueos concretos, con archivo o zona afectada.
- `P1`: mejoras importantes.
- `P2`: limpieza o deuda aceptable.
- `Plan recomendado`: pasos ordenados para Codex.
- `Pruebas sugeridas`: comandos o fixtures que deberían existir.

## Estado Git local reportado por Codex

```text
{branch}

{head}

{status}

{latest}

{diff}
```

## Guía de revisión del repo

```markdown
{safe_read("REVIEW.md")}
```

## Estado actual documentado

```markdown
{safe_read("docs/review/status.md")}
```

## Limitaciones conocidas

```markdown
{safe_read("docs/review/known-limitations.md")}
```

## Arquitectura

```markdown
{safe_read("docs/review/architecture-map.md")}
```

## Log de validación reportado

```markdown
{safe_read("docs/review/validation-log.md")}
```

## Checklist de revisión

```markdown
{safe_read("docs/review/reviewer-checklist.md")}
```
"""


def copy_to_clipboard(text: str) -> None:
    completed = subprocess.run(
        ["clip.exe"],
        input=text,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("No se pudo copiar el prompt al portapapeles con clip.exe.")


def read_clipboard() -> str:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "No se pudo leer el portapapeles.")
    return completed.stdout.strip()


def create_round(args: argparse.Namespace) -> int:
    round_id = args.round_id or current_round_id()
    prompt = build_prompt(round_id, args.focus)
    if args.dry_run:
        print(prompt)
        return 0

    destination = round_path(round_id)
    destination.mkdir(parents=True, exist_ok=False)

    (destination / "prompt.md").write_text(prompt + "\n", encoding="utf-8")
    (destination / "response.md").write_text(
        "# ChatGPT Pro response\n\nPega aqui la respuesta completa si no se captura automaticamente.\n",
        encoding="utf-8",
    )
    (destination / "backlog.md").write_text(
        "# Review Backlog\n\nPendiente de ingerir respuesta.\n",
        encoding="utf-8",
    )

    if args.copy:
        copy_to_clipboard(prompt)

    print(destination)
    if args.copy:
        print("Prompt copied to clipboard.")
    return 0


def classify_line(line: str) -> str | None:
    normalized = line.strip()
    if re.search(r"\bP0\b|bloque|blocker|no-go|no go", normalized, re.IGNORECASE):
        return "P0"
    if re.search(r"\bP1\b|importante|should|deberia|debería", normalized, re.IGNORECASE):
        return "P1"
    if re.search(r"\bP2\b|limpieza|deuda|nice", normalized, re.IGNORECASE):
        return "P2"
    return None


def extract_backlog(response: str) -> dict[str, list[str]]:
    backlog = {"P0": [], "P1": [], "P2": [], "Plan": [], "Tests": []}
    active: str | None = None

    for raw_line in response.splitlines():
        line = raw_line.rstrip()
        heading = line.strip().lstrip("#").strip().rstrip(":").lower()
        if heading in {"p0", "p0 bloqueos", "hallazgos p0"}:
            active = "P0"
            continue
        if heading in {"p1", "p1 mejoras", "hallazgos p1"}:
            active = "P1"
            continue
        if heading in {"p2", "p2 limpieza", "hallazgos p2"}:
            active = "P2"
            continue
        if "plan recomendado" in heading:
            active = "Plan"
            continue
        if "pruebas sugeridas" in heading or "tests sugeridos" in heading:
            active = "Tests"
            continue

        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "6.")):
            bucket = active or classify_line(stripped) or "P1"
            backlog[bucket].append(stripped)

    return backlog


def render_backlog(round_id: str, response: str) -> str:
    backlog = extract_backlog(response)
    lines = [
        "# Review Backlog",
        "",
        f"Round: `{round_id}`",
        "",
        "Source: `response.md`",
        "",
    ]
    for bucket in ("P0", "P1", "P2", "Plan", "Tests"):
        lines.append(f"## {bucket}")
        lines.append("")
        items = backlog[bucket]
        if items:
            lines.extend(items)
        else:
            lines.append("(sin elementos detectados)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def ingest_round(args: argparse.Namespace) -> int:
    target = round_path(args.round_id)
    if not target.exists():
        raise FileNotFoundError(target)

    response_path = target / "response.md"
    if args.from_clipboard:
        response = read_clipboard()
        response_path.write_text(response + "\n", encoding="utf-8")
    else:
        response = response_path.read_text(encoding="utf-8")

    if "Pega aqui la respuesta completa" in response or not response.strip():
        raise ValueError(f"No hay respuesta real para ingerir en {response_path}.")

    (target / "backlog.md").write_text(render_backlog(args.round_id, response), encoding="utf-8")
    print(target / "backlog.md")
    return 0


def list_rounds(_: argparse.Namespace) -> int:
    if not ROUNDS_ROOT.exists():
        print("(no rounds)")
        return 0
    for path in sorted(ROUNDS_ROOT.iterdir(), reverse=True):
        if path.is_dir():
            print(path.name)
    return 0


def self_test(_: argparse.Namespace) -> int:
    response = """# Dictamen

Aprobado con cambios.

## P0

- `python/compiler/function_graph.py` no existe.

## P1

- Añadir test de segmentos en discontinuidades.

## Plan recomendado

1. Crear compilador.
2. Añadir fixtures.

## Pruebas sugeridas

- `python scripts/run_smoke_tests.py`
"""
    backlog = extract_backlog(response)
    assert backlog["P0"] == ["- `python/compiler/function_graph.py` no existe."]
    assert backlog["P1"] == ["- Añadir test de segmentos en discontinuidades."]
    assert backlog["Plan"] == ["1. Crear compilador.", "2. Añadir fixtures."]
    assert backlog["Tests"] == ["- `python scripts/run_smoke_tests.py`"]
    prompt = build_prompt("self-test", "Comprobar generacion de prompt.")
    assert "Solicitud de revisión para ChatGPT Pro" in prompt
    assert "Guía de revisión del repo" in prompt
    print("pro review cycle self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and ingest ChatGPT Pro review rounds.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a review round and prompt.")
    create.add_argument("--round-id", help="Stable round id. Defaults to timestamp.")
    create.add_argument("--focus", default="Revisar el estado actual y proponer la siguiente iteracion tecnica.")
    create.add_argument("--copy", action="store_true", help="Copy prompt to Windows clipboard.")
    create.add_argument("--dry-run", action="store_true", help="Print prompt without writing a round.")
    create.set_defaults(func=create_round)

    ingest = subparsers.add_parser("ingest", help="Ingest ChatGPT Pro response into backlog.")
    ingest.add_argument("round_id")
    ingest.add_argument("--from-clipboard", action="store_true", help="Read response from Windows clipboard.")
    ingest.set_defaults(func=ingest_round)

    list_cmd = subparsers.add_parser("list", help="List review rounds.")
    list_cmd.set_defaults(func=list_rounds)

    self_test_cmd = subparsers.add_parser("self-test", help="Run local parser checks.")
    self_test_cmd.set_defaults(func=self_test)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"pro review cycle failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

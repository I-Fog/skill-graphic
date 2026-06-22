from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUNDS_ROOT = ROOT / "docs" / "review" / "pro-rounds"
ROUND_ID_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,79}$")
MAX_DIFF_CHARS = 140000
MAX_UNTRACKED_TEXT_CHARS = 60000
PLACEHOLDER_RESPONSE = "# ChatGPT Pro response\n\nPega aqui la respuesta completa si no se captura automaticamente.\n"
PLACEHOLDER_BACKLOG = "# Review Backlog\n\nPendiente de ingerir respuesta.\n"
SAFE_POPUP_BUTTONS = {
    "Aceptar",
    "Ahora no",
    "Continuar",
    "Entendido",
    "Got it",
    "No gracias",
    "Not now",
    "Omitir",
    "Skip",
}


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
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{completed.stderr.strip()}")
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
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%SZ")
    return f"{timestamp}-{secrets.token_hex(3)}"


def round_path(round_id: str) -> Path:
    if not ROUND_ID_PATTERN.fullmatch(round_id):
        raise ValueError(f"Invalid round_id: {round_id!r}")
    root = ROUNDS_ROOT.resolve()
    path = (root / round_id).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"round_id escapes pro-rounds: {round_id!r}")
    return path


def sha256_text(text: str) -> str:
    canonical = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(4)}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
    temporary.replace(path)


def read_round_manifest(round_id: str) -> dict:
    path = round_path(round_id) / "round.json"
    return json.loads(path.read_text(encoding="utf-8"))


def write_round_manifest(round_id: str, manifest: dict) -> None:
    atomic_write_text(round_path(round_id) / "round.json", json.dumps(manifest, ensure_ascii=True, indent=2) + "\n")


def update_round_state(round_id: str, state: str, **extra: object) -> None:
    manifest = read_round_manifest(round_id)
    manifest["state"] = state
    manifest["updated_at"] = dt.datetime.now(dt.UTC).isoformat()
    manifest.update(extra)
    write_round_manifest(round_id, manifest)


def git_value(command: list[str]) -> str:
    completed = run(command)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{completed.stderr.strip()}")
    return completed.stdout.strip()


def dirty_patch_text() -> str:
    patch = command_text(["git", "diff", "--binary"])
    staged_patch = command_text(["git", "diff", "--cached", "--binary"])
    untracked = describe_untracked_files()
    payload = f"{patch}\n\n{staged_patch}\n\n{untracked}"
    if len(payload) <= MAX_DIFF_CHARS:
        return payload
    digest = sha256_text(payload)
    return payload[:MAX_DIFF_CHARS] + f"\n\n[TRUNCATED dirty patch: sha256={digest}, chars={len(payload)}]\n"


def describe_untracked_files() -> str:
    listing = git_value(["git", "ls-files", "--others", "--exclude-standard"])
    if not listing:
        return "$ git ls-files --others --exclude-standard\n(no output)"

    blocks = ["$ git ls-files --others --exclude-standard", listing]
    for relative in listing.splitlines():
        path = (ROOT / relative).resolve()
        if ROOT.resolve() not in path.parents and path != ROOT.resolve():
            blocks.append(f"\n## {relative}\n[skipped: path escapes repository]")
            continue
        if not path.is_file():
            blocks.append(f"\n## {relative}\n[skipped: not a regular file]")
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) > MAX_UNTRACKED_TEXT_CHARS or b"\x00" in data:
            blocks.append(f"\n## {relative}\n[content omitted: bytes={len(data)}, sha256={digest}]")
            continue
        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError:
            blocks.append(f"\n## {relative}\n[content omitted: bytes={len(data)}, sha256={digest}, non-utf8]")
            continue
        blocks.append(f"\n## {relative}\nsha256: {digest}\n```text\n{content.rstrip()}\n```")
    return "\n".join(blocks)


def new_manifest(round_id: str, focus: str, nonce: str, prompt: str, transport: str) -> dict:
    return {
        "round_id": round_id,
        "nonce": nonce,
        "state": "created",
        "transport": transport,
        "focus": focus,
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "updated_at": dt.datetime.now(dt.UTC).isoformat(),
        "git": {
            "branch": git_value(["git", "branch", "--show-current"]),
            "head": git_value(["git", "rev-parse", "HEAD"]),
            "dirty_status": git_value(["git", "status", "--short"]),
        },
        "hashes": {
            "prompt_sha256": sha256_text(prompt.rstrip() + "\n"),
        },
    }


def assert_response_identity(round_id: str, response: str) -> dict:
    manifest = read_round_manifest(round_id)
    nonce = str(manifest.get("nonce", ""))
    lines = [line.strip() for line in response.lstrip().splitlines() if line.strip()]
    expected_prefix = [f"ROUND_ID: {round_id}", f"NONCE: {nonce}"]
    if lines[:2] != expected_prefix:
        raise ValueError(f"La respuesta no empieza con ROUND_ID/NONCE de la ronda {round_id}.")
    if lines[-1:] != [f"END_REVIEW: {nonce}"]:
        raise ValueError(f"La respuesta no termina con END_REVIEW de la ronda {round_id}.")
    prompt_path = round_path(round_id) / "prompt.md"
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8")
        if response.strip() == prompt.strip():
            raise ValueError("La respuesta coincide con el prompt; no es un dictamen externo.")
        prompt_hash = manifest.get("hashes", {}).get("prompt_sha256")
        if prompt_hash and prompt_hash == sha256_text(response.rstrip() + "\n"):
            raise ValueError("La respuesta tiene el mismo hash que el prompt.")
    if not looks_like_review_response(response):
        raise ValueError("La respuesta no tiene forma de dictamen/revision.")
    if not has_required_review_sections(response):
        raise ValueError("La respuesta no contiene todas las secciones obligatorias.")
    return manifest


def build_prompt(round_id: str, focus: str, nonce: str) -> str:
    repo_url = "https://github.com/I-Fog/skill-graphic"
    status = command_text(["git", "status", "--short"])
    branch = command_text(["git", "branch", "--show-current"])
    head = command_text(["git", "rev-parse", "HEAD"])
    latest = command_text(["git", "show", "--stat", "--oneline", "--decorate", "-1"])
    diff = command_text(["git", "diff", "--stat"])
    dirty_patch = dirty_patch_text()

    return f"""# Solicitud de revisión para ChatGPT Pro

Repositorio: {repo_url}
Rama esperada: `codex/skill-graphic-mvp`
Ronda: `{round_id}`
Nonce de ronda: `{nonce}`

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

Empieza tu respuesta exactamente con:

```text
ROUND_ID: {round_id}
NONCE: {nonce}
```

Luego devuelve:

- `Dictamen`: aprobado, aprobado con cambios, o cambios solicitados.
- `P0`: bloqueos concretos, con archivo o zona afectada.
- `P1`: mejoras importantes.
- `P2`: limpieza o deuda aceptable.
- `Plan recomendado`: pasos ordenados para Codex.
- `Pruebas sugeridas`: comandos o fixtures que deberían existir.

Termina tu respuesta exactamente con:

```text
END_REVIEW: {nonce}
```

## Estado Git local reportado por Codex

```text
{branch}

{head}

{status}

{latest}

{diff}
```

## Diff completo local no commiteado

````diff
{dirty_patch}
````

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


def open_url(url: str) -> None:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Start-Process {url!r}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"No se pudo abrir {url}.")


def looks_like_review_response(text: str) -> bool:
    if len(text.strip()) < 200:
        return False
    markers = 0
    for pattern in (
        r"\bDictamen\b",
        r"\bP0\b",
        r"\bP1\b",
        r"Plan recomendado",
        r"Pruebas sugeridas",
        r"cambios solicitados",
        r"aprobado",
    ):
        if re.search(pattern, text, re.IGNORECASE):
            markers += 1
    return markers >= 2


def has_required_review_sections(text: str) -> bool:
    required = (
        "Dictamen",
        "P0",
        "P1",
        "P2",
        "Plan recomendado",
        "Pruebas sugeridas",
    )
    return all(
        re.search(rf"^\s{{0,3}}#{{1,6}}\s+{re.escape(heading)}\s*$", text, re.IGNORECASE | re.MULTILINE)
        for heading in required
    )


def side_panel_descendants():
    try:
        from pywinauto import Desktop
    except ImportError as exc:
        raise RuntimeError("pywinauto is required for --transport uia.") from exc

    window = Desktop(backend="uia").window(title="Codex")
    if not window.exists():
        raise RuntimeError("Codex window was not found for UIA transport.")
    return window, window.descendants()


def dismiss_safe_chatgpt_popups() -> None:
    window, descendants = side_panel_descendants()
    for child in descendants:
        text = (child.window_text() or "").strip()
        rect = child.rectangle()
        if rect.left < 1000 or text not in SAFE_POPUP_BUTTONS:
            continue
        try:
            child.click_input()
            time.sleep(0.5)
            window.set_focus()
            return
        except Exception:
            continue


def find_chatgpt_prompt_edit(descendants):
    for child in descendants:
        info = child.element_info
        rect = child.rectangle()
        if info.automation_id == "prompt-textarea" and rect.left >= 1000:
            return child
    return None


def find_chatgpt_submit_button(descendants):
    for child in descendants:
        info = child.element_info
        rect = child.rectangle()
        if info.automation_id == "composer-submit-button" and rect.left >= 1000:
            return child
    return None


def is_uia_generation_active() -> bool:
    _, descendants = side_panel_descendants()
    for child in descendants:
        text = (child.window_text() or "").strip().lower()
        rect = child.rectangle()
        if rect.left >= 1000 and ("detener respuesta" in text or "stop generating" in text):
            return True
    return False


def send_prompt_uia(prompt: str) -> None:
    try:
        from pywinauto import keyboard
    except ImportError as exc:
        raise RuntimeError("pywinauto is required for --transport uia.") from exc

    dismiss_safe_chatgpt_popups()
    copy_to_clipboard(prompt)
    window, descendants = side_panel_descendants()
    window.set_focus()
    time.sleep(0.3)

    prompt_edit = find_chatgpt_prompt_edit(descendants)
    if prompt_edit is None:
        raise RuntimeError("ChatGPT prompt textarea was not found in the integrated browser panel.")

    prompt_edit.click_input()
    time.sleep(0.2)
    keyboard.send_keys("^a")
    time.sleep(0.1)
    keyboard.send_keys("^v")
    time.sleep(0.5)

    dismiss_safe_chatgpt_popups()
    _, descendants = side_panel_descendants()
    submit = find_chatgpt_submit_button(descendants)
    if submit is None:
        raise RuntimeError("ChatGPT submit button was not found after pasting the prompt.")

    submit.click_input()
    time.sleep(1.0)
    _, descendants = side_panel_descendants()
    active_submit = find_chatgpt_submit_button(descendants)
    if active_submit is None:
        return
    submit_text = (active_submit.window_text() or "").strip().lower()
    if "enviar" in submit_text or "send" in submit_text:
        raise RuntimeError("ChatGPT submit button still looks idle; the prompt may not have been sent.")


def copy_latest_review_response_uia(round_id: str) -> str | None:
    try:
        from pywinauto import keyboard
    except ImportError as exc:
        raise RuntimeError("pywinauto is required for --transport uia.") from exc

    if is_uia_generation_active():
        return None
    copy_to_clipboard("__skill_graphic_waiting_for_response__")
    window, _ = side_panel_descendants()
    window.set_focus()
    keyboard.send_keys("^{END}")
    time.sleep(0.5)
    _, descendants = side_panel_descendants()
    copy_buttons = []
    for child in descendants:
        text = (child.window_text() or "").strip()
        rect = child.rectangle()
        if rect.left >= 1000 and text in {"Copiar respuesta", "Copy response"}:
            copy_buttons.append(child)
    if not copy_buttons:
        return None

    copy_buttons.sort(key=lambda item: item.rectangle().top, reverse=True)
    try:
        copy_buttons[0].click_input()
    except Exception:
        return None
    time.sleep(0.5)
    copied = read_clipboard()
    if round_id in copied and looks_like_review_response(copied):
        return copied
    return None


def extract_latest_review_response_uia(round_id: str) -> str | None:
    _, descendants = side_panel_descendants()
    seen_round_marker = False
    candidates: list[str] = []
    ignored = {
        "Copiar",
        "Copiar respuesta",
        "Editar mensaje",
        "Tus acciones de mensaje",
        "Acciones de respuesta",
        "ChatGPT puede cometer errores. Considera verificar la información importante.",
        "Pregunta lo que quieras",
    }

    for child in descendants:
        info = child.element_info
        rect = child.rectangle()
        if rect.left < 1000:
            continue

        text = (child.window_text() or "").strip()
        if not text:
            continue
        if round_id in text:
            seen_round_marker = True
            continue
        if not seen_round_marker:
            continue
        if info.automation_id == "prompt-textarea":
            break
        if text in ignored or info.control_type == "Button":
            continue
        if len(text) >= 120:
            candidates.append(text)

    review_like = [candidate for candidate in candidates if looks_like_review_response(candidate)]
    if review_like:
        return max(review_like, key=len)
    if candidates:
        return max(candidates, key=len)
    return None


def wait_for_uia_response(round_id: str, timeout_seconds: int, poll_seconds: float) -> str:
    deadline = time.monotonic() + timeout_seconds
    last_candidate = ""
    stable_count = 0
    while time.monotonic() < deadline:
        time.sleep(poll_seconds)
        if is_uia_generation_active():
            stable_count = 0
            continue
        candidate = copy_latest_review_response_uia(round_id) or extract_latest_review_response_uia(round_id)
        if not candidate or not looks_like_review_response(candidate):
            stable_count = 0
            continue
        try:
            assert_response_identity(round_id, candidate)
        except ValueError:
            stable_count = 0
            continue
        if candidate == last_candidate:
            stable_count += 1
        else:
            last_candidate = candidate
            stable_count = 1
        if stable_count >= 2:
            return candidate

    raise TimeoutError(
        f"No se detecto una respuesta valida de ChatGPT Pro antes de {timeout_seconds} segundos."
    )


def create_round(args: argparse.Namespace) -> int:
    round_id = args.round_id or current_round_id()
    round_path(round_id)
    nonce = secrets.token_hex(8)
    prompt = build_prompt(round_id, args.focus, nonce)
    if args.dry_run:
        print(prompt)
        return 0

    destination = round_path(round_id)
    destination.mkdir(parents=True, exist_ok=False)

    atomic_write_text(destination / "prompt.md", prompt.rstrip() + "\n")
    atomic_write_text(destination / "response.md", PLACEHOLDER_RESPONSE)
    atomic_write_text(destination / "backlog.md", PLACEHOLDER_BACKLOG)
    write_round_manifest(round_id, new_manifest(round_id, args.focus, nonce, prompt, "clipboard"))

    if args.copy:
        copy_to_clipboard(prompt)
        update_round_state(round_id, "prompt_copied")

    print(destination)
    if args.copy:
        print("Prompt copied to clipboard.")
    return 0


def create_round_files(round_id: str, focus: str, copy: bool, transport: str) -> Path:
    nonce = secrets.token_hex(8)
    prompt = build_prompt(round_id, focus, nonce)
    destination = round_path(round_id)
    destination.mkdir(parents=True, exist_ok=False)
    atomic_write_text(destination / "prompt.md", prompt.rstrip() + "\n")
    atomic_write_text(destination / "response.md", PLACEHOLDER_RESPONSE)
    atomic_write_text(destination / "backlog.md", PLACEHOLDER_BACKLOG)
    write_round_manifest(round_id, new_manifest(round_id, focus, nonce, prompt, transport))
    if copy:
        copy_to_clipboard(prompt)
        update_round_state(round_id, "prompt_copied")
    return destination


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


def store_response_and_backlog(round_id: str, response: str) -> Path:
    target = round_path(round_id)
    if not target.exists():
        raise FileNotFoundError(target)
    if "Pega aqui la respuesta completa" in response or not response.strip():
        raise ValueError(f"No hay respuesta real para ingerir en {target / 'response.md'}.")
    manifest = assert_response_identity(round_id, response)
    rendered_backlog = render_backlog(round_id, response)
    atomic_write_text(target / "response.md", response.rstrip() + "\n")
    backlog_path = target / "backlog.md"
    atomic_write_text(backlog_path, rendered_backlog)
    manifest.setdefault("hashes", {})["response_sha256"] = sha256_text(response.rstrip() + "\n")
    manifest.setdefault("hashes", {})["backlog_sha256"] = sha256_text(rendered_backlog)
    manifest["state"] = "ingested"
    manifest["updated_at"] = dt.datetime.now(dt.UTC).isoformat()
    write_round_manifest(round_id, manifest)
    return backlog_path


def ingest_round(args: argparse.Namespace) -> int:
    target = round_path(args.round_id)
    if not target.exists():
        raise FileNotFoundError(target)

    response_path = target / "response.md"
    if args.from_clipboard:
        response = read_clipboard()
    else:
        response = response_path.read_text(encoding="utf-8")

    backlog_path = store_response_and_backlog(args.round_id, response)
    print(backlog_path)
    return 0


def ingest_text(round_id: str, response: str) -> Path:
    return store_response_and_backlog(round_id, response)


def run_round(args: argparse.Namespace) -> int:
    round_id = args.round_id or current_round_id()
    initial_clipboard = read_clipboard() if args.transport == "clipboard" and args.wait_clipboard else ""
    destination = create_round_files(
        round_id,
        args.focus,
        copy=args.transport == "clipboard",
        transport=args.transport,
    )
    prompt_path = destination / "prompt.md"
    print(destination)
    if args.transport == "clipboard":
        print("Prompt copied to clipboard.")
    print(f"Prompt path: {prompt_path}")

    if args.open_url:
        open_url(args.open_url)
        print(f"Opened: {args.open_url}")

    if args.transport == "uia":
        prompt = prompt_path.read_text(encoding="utf-8").strip()
        send_prompt_uia(prompt)
        update_round_state(round_id, "prompt_sent")
        print("Prompt sent through integrated browser UIA transport.")
        response = wait_for_uia_response(round_id, args.timeout_seconds, args.poll_seconds)
        backlog_path = ingest_text(round_id, response)
        print(backlog_path)
        return 0

    if not args.wait_clipboard:
        print("Waiting disabled. Paste the answer into response.md or run ingest later.")
        return 0

    deadline = time.monotonic() + args.timeout_seconds
    print("Waiting for a ChatGPT Pro response on the clipboard...")
    while time.monotonic() < deadline:
        time.sleep(args.poll_seconds)
        current = read_clipboard()
        if current == initial_clipboard:
            continue
        if current == prompt_path.read_text(encoding="utf-8").strip():
            continue
        if not looks_like_review_response(current):
            continue
        backlog_path = ingest_text(round_id, current)
        print(backlog_path)
        return 0

    raise TimeoutError(
        f"No se detecto una respuesta valida en el portapapeles antes de {args.timeout_seconds} segundos."
    )


def list_rounds(_: argparse.Namespace) -> int:
    if not ROUNDS_ROOT.exists():
        print("(no rounds)")
        return 0
    for path in sorted(ROUNDS_ROOT.iterdir(), reverse=True):
        if path.is_dir():
            print(path.name)
    return 0


def verify_round(args: argparse.Namespace) -> int:
    target = round_path(args.round_id)
    manifest = read_round_manifest(args.round_id)
    if manifest.get("round_id") != args.round_id:
        raise ValueError("round.json no coincide con el round_id solicitado.")
    if manifest.get("state") not in {"ingested", "verified"}:
        raise ValueError("round.json debe estar en estado ingested o verified antes de verificar.")
    prompt = (target / "prompt.md").read_text(encoding="utf-8")
    response = (target / "response.md").read_text(encoding="utf-8")
    backlog = (target / "backlog.md").read_text(encoding="utf-8")

    expected_prompt_hash = manifest.get("hashes", {}).get("prompt_sha256")
    if expected_prompt_hash != sha256_text(prompt.rstrip() + "\n"):
        raise ValueError("prompt.md no coincide con round.json hashes.prompt_sha256.")
    assert_response_identity(args.round_id, response)
    if "Pega aqui la respuesta completa" in response:
        raise ValueError("response.md sigue siendo placeholder.")
    if "Pendiente de ingerir respuesta" in backlog:
        raise ValueError("backlog.md sigue siendo placeholder.")
    expected_backlog = render_backlog(args.round_id, response)
    if backlog != expected_backlog:
        raise ValueError("backlog.md no coincide con render_backlog(response.md).")

    extracted = extract_backlog(response)
    if not any(extracted[bucket] for bucket in ("P0", "P1", "P2", "Plan", "Tests")):
        raise ValueError("No se detectaron elementos de backlog en la respuesta.")

    expected_response_hash = manifest.get("hashes", {}).get("response_sha256")
    if not expected_response_hash:
        raise ValueError("round.json no contiene hashes.response_sha256.")
    if expected_response_hash != sha256_text(response.rstrip() + "\n"):
        raise ValueError("response.md no coincide con round.json hashes.response_sha256.")
    expected_backlog_hash = manifest.get("hashes", {}).get("backlog_sha256")
    if not expected_backlog_hash:
        raise ValueError("round.json no contiene hashes.backlog_sha256.")
    if expected_backlog_hash != sha256_text(backlog):
        raise ValueError("backlog.md no coincide con round.json hashes.backlog_sha256.")

    manifest["state"] = "verified"
    manifest["updated_at"] = dt.datetime.now(dt.UTC).isoformat()
    write_round_manifest(args.round_id, manifest)
    print(f"round verified: {target}")
    return 0


def self_test(_: argparse.Namespace) -> int:
    round_id = "self-test"
    nonce = "nonce-test"
    response = f"""ROUND_ID: {round_id}
NONCE: {nonce}

# Dictamen

Aprobado con cambios.

## P0

- `python/compiler/function_graph.py` no existe.

## P1

- Añadir test de segmentos en discontinuidades.

## P2

- Documentar deuda menor.

## Plan recomendado

1. Crear compilador.
2. Añadir fixtures.

## Pruebas sugeridas

- `python scripts/run_smoke_tests.py`

END_REVIEW: {nonce}
"""
    backlog = extract_backlog(response)
    assert backlog["P0"] == ["- `python/compiler/function_graph.py` no existe."]
    assert backlog["P1"] == ["- Añadir test de segmentos en discontinuidades."]
    assert backlog["Plan"] == ["1. Crear compilador.", "2. Añadir fixtures."]
    assert backlog["Tests"] == ["- `python scripts/run_smoke_tests.py`"]
    prompt = build_prompt(round_id, "Comprobar generacion de prompt.", nonce)
    assert "Solicitud de revisión para ChatGPT Pro" in prompt
    assert "Guía de revisión del repo" in prompt
    assert f"ROUND_ID: {round_id}" in prompt
    assert f"NONCE: {nonce}" in prompt
    assert f"END_REVIEW: {nonce}" in prompt
    assert looks_like_review_response(response)
    assert not looks_like_review_response("texto corto")
    assert round_path("safe-round_1.2").name == "safe-round_1.2"
    try:
        round_path("../../escape")
    except ValueError:
        pass
    else:
        raise AssertionError("round_path accepted an escaping id")
    temp_round = f"self-test-{secrets.token_hex(3)}"
    temp_target = round_path(temp_round)
    temp_nonce = "nonce-temp"
    temp_prompt = build_prompt(temp_round, "Comprobar identidad.", temp_nonce)
    temp_response = response.replace(round_id, temp_round).replace(nonce, temp_nonce)
    try:
        temp_target.mkdir(parents=True, exist_ok=False)
        atomic_write_text(temp_target / "prompt.md", temp_prompt.rstrip() + "\n")
        atomic_write_text(temp_target / "response.md", PLACEHOLDER_RESPONSE)
        atomic_write_text(temp_target / "backlog.md", PLACEHOLDER_BACKLOG)
        write_round_manifest(temp_round, new_manifest(temp_round, "Comprobar identidad.", temp_nonce, temp_prompt, "self-test"))
        assert_response_identity(temp_round, temp_response)
        try:
            assert_response_identity(temp_round, temp_prompt)
        except ValueError:
            pass
        else:
            raise AssertionError("prompt accepted as response")
        try:
            assert_response_identity(temp_round, "\n" + temp_response.replace(f"ROUND_ID: {temp_round}", "texto previo"))
        except ValueError:
            pass
        else:
            raise AssertionError("non-anchored round markers accepted")
        try:
            assert_response_identity(temp_round, temp_response.replace(f"\nEND_REVIEW: {temp_nonce}\n", "\n"))
        except ValueError:
            pass
        else:
            raise AssertionError("response without END_REVIEW accepted")
        try:
            assert_response_identity(temp_round, temp_response.replace("## P2\n\n- Documentar deuda menor.\n\n", ""))
        except ValueError:
            pass
        else:
            raise AssertionError("response without required heading accepted")
        before_invalid = (temp_target / "response.md").read_text(encoding="utf-8")
        try:
            store_response_and_backlog(temp_round, "ROUND_ID: wrong\nNONCE: wrong\n\n## Dictamen\n\nMal\n")
        except ValueError:
            pass
        else:
            raise AssertionError("invalid response stored")
        assert (temp_target / "response.md").read_text(encoding="utf-8") == before_invalid
        store_response_and_backlog(temp_round, temp_response)
        verify_round(argparse.Namespace(round_id=temp_round))
        atomic_write_text(temp_target / "backlog.md", "# Review Backlog\n\nmanipulado\n")
        try:
            verify_round(argparse.Namespace(round_id=temp_round))
        except ValueError:
            pass
        else:
            raise AssertionError("modified backlog accepted")
        store_response_and_backlog(temp_round, temp_response)
        manifest = read_round_manifest(temp_round)
        manifest["hashes"].pop("response_sha256", None)
        write_round_manifest(temp_round, manifest)
        try:
            verify_round(argparse.Namespace(round_id=temp_round))
        except ValueError:
            pass
        else:
            raise AssertionError("missing response hash accepted")
        store_response_and_backlog(temp_round, temp_response)
        manifest = read_round_manifest(temp_round)
        manifest["state"] = "created"
        write_round_manifest(temp_round, manifest)
        try:
            verify_round(argparse.Namespace(round_id=temp_round))
        except ValueError:
            pass
        else:
            raise AssertionError("invalid manifest state accepted")
    finally:
        if temp_target.exists():
            shutil.rmtree(temp_target)
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

    run_cmd = subparsers.add_parser("run", help="Create a round, copy the prompt, wait for clipboard response, and ingest it.")
    run_cmd.add_argument("--round-id", help="Stable round id. Defaults to timestamp.")
    run_cmd.add_argument("--focus", default="Revisar el estado actual y proponer la siguiente iteracion tecnica.")
    run_cmd.add_argument("--open-url", help="Optional ChatGPT conversation URL to open.")
    run_cmd.add_argument("--transport", choices=["clipboard", "uia"], default="clipboard")
    run_cmd.add_argument("--wait-clipboard", action="store_true", help="Poll clipboard until a review response appears.")
    run_cmd.add_argument("--timeout-seconds", type=int, default=1800)
    run_cmd.add_argument("--poll-seconds", type=float, default=5.0)
    run_cmd.set_defaults(func=run_round)

    list_cmd = subparsers.add_parser("list", help="List review rounds.")
    list_cmd.set_defaults(func=list_rounds)

    verify_cmd = subparsers.add_parser("verify", help="Verify round identity, hashes, response, and backlog.")
    verify_cmd.add_argument("round_id")
    verify_cmd.set_defaults(func=verify_round)

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

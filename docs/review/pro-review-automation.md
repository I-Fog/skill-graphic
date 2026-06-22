# ChatGPT Pro Review Automation

This workflow turns the external ChatGPT Pro review loop into a repeatable round:

```text
Codex changes repo
  -> Codex validates locally
  -> Codex creates a Pro review prompt
  -> ChatGPT Pro returns a dictamen
  -> Codex ingests the response into backlog
  -> Codex applies the next changes
```

The transport layer can be UI Automation against the integrated browser, manual clipboard, or a future API-backed adapter. The repo contract lives in `scripts/pro_review_cycle.py`; browser control is intentionally outside the math validators and renderers.

For project-agnostic supervision, use the global skill:

```powershell
codex-supervise run --transport uia --scope function-renderer --focus "Revisa el scope actual y dime si queda algun P0."
```

The global route stores rounds in `.codex-supervision/pro-rounds/` and reads this repo's `codex-supervision.json` scope map. The local `scripts/pro_review_cycle.py` remains as the repo-specific compatibility route.

If a terminal has not reloaded PATH yet, call the launcher directly:

```powershell
& "$env:USERPROFILE\.codex\bin\codex-supervise.cmd" run --transport uia --scope function-renderer --focus "Revisa el scope actual y dime si queda algun P0."
```

To supervise a repo while the shell is somewhere else, pass the root for that command:

```powershell
codex-supervise pack --root "D:\PERSONAL\chatgpt\skills\skill_graphic" --scope function-renderer
```

## Commands

Run a review round through the integrated browser panel:

```powershell
python scripts/pro_review_cycle.py run --transport uia --scope function-renderer --focus "Revisa solo el renderer de funciones y dime si queda algun P0 antes de commit/push."
```

This creates a compact scoped packet, writes a reproducible packet snapshot, finds the ChatGPT composer in the Codex side browser, pastes the prompt, sends it, waits for a review-shaped response, writes `response.md`, and regenerates `backlog.md`.

Create a compact review packet without sending it:

```powershell
python scripts/pro_review_cycle.py pack --scope pro-loop --focus "Revisa el protocolo Codex-Pro y dime si queda algun P0."
```

Scopes:

- `pro-loop`: review automation, prompt protocol, and skill workflow docs.
- `function-renderer`: function render model, SVG renderer, generator, smoke, and browser spec.
- `docs`: public review docs and status files.
- `all`: compact union of the scoped files.

Use a full packet only for broad audits where the reviewer must inspect the entire dirty diff:

```powershell
python scripts/pro_review_cycle.py create --packet full --copy --focus "Auditoria amplia del estado actual."
```

Create a review round without sending it:

```powershell
python scripts/pro_review_cycle.py create --scope function-renderer --copy --focus "Revisa los cambios recientes y dime el siguiente P0."
```

The local compatibility route writes:

- `docs/review/pro-rounds/<round-id>/prompt.md`
- `docs/review/pro-rounds/<round-id>/response.md`
- `docs/review/pro-rounds/<round-id>/backlog.md`
- `docs/review/pro-rounds/<round-id>/round.json`
- `docs/review/pro-rounds/<round-id>/packet/manifest.json`
- `docs/review/pro-rounds/<round-id>/packet/scoped.diff` or `packet/dirty.patch`
- `docs/review/pro-rounds/<round-id>/packet/files/`

If `--copy` is used, the prompt is copied to the Windows clipboard so it can be pasted into ChatGPT Pro.

Ingest a response pasted into the clipboard:

```powershell
python scripts/pro_review_cycle.py ingest <round-id> --from-clipboard
```

Or paste the response into `response.md` and run:

```powershell
python scripts/pro_review_cycle.py ingest <round-id>
```

List existing rounds:

```powershell
python scripts/pro_review_cycle.py list
```

Validate the local parser without creating a round:

```powershell
python scripts/pro_review_cycle.py self-test
```

Verify a completed round:

```powershell
python scripts/pro_review_cycle.py verify <round-id>
```

Preview the prompt without writing files:

```powershell
python scripts/pro_review_cycle.py create --dry-run
```

## Round Artifacts

| Route | Command family | Round directory |
| --- | --- | --- |
| Global supervisor | `codex-supervise ...` | `.codex-supervision/pro-rounds/<round-id>/` |
| Local compatibility | `python scripts/pro_review_cycle.py ...` | `docs/review/pro-rounds/<round-id>/` |

- `prompt.md`: compact scoped packet by default. Full packets include Git state, review docs, limitations, architecture map, validation log, checklist, and the broader dirty diff.
- `response.md`: raw ChatGPT Pro answer.
- `backlog.md`: extracted `P0`, `P1`, `P2`, plan, and tests from the response.
- `round.json`: round state, nonce, transport, Git head/status, selected scope, response scope, included files, `packet_snapshot` metadata, and prompt/response hashes.
- `packet/manifest.json`: immutable packet manifest with copied-file hashes, prompt hash, diff hash, packet type, selected scope, and response scope.
- `packet/files/`: exact copies of the files whose content was sent in the packet.
- `packet/scoped.diff` or `packet/dirty.patch`: the diff text used by the packet.

Keep round artifacts out of reusable skill references. Global rounds are ignored through `.codex-supervision/`; local compatibility rounds should remain review evidence and should only be committed when intentionally needed as public evidence.

## Browser Adapter Boundary

The intended automated route is:

```powershell
python scripts/pro_review_cycle.py run --transport uia --scope function-renderer --timeout-seconds 1800
```

It performs:

1. Create a compact scoped round.
2. Copy and send `prompt.md` into the active ChatGPT Pro conversation in the integrated browser panel.
3. Wait for generation to stabilize.
4. Save the answer to `response.md`.
5. Generate `backlog.md`.

Fallback: clipboard transport. It preserves the same artifacts and lets Codex continue the loop when UI Automation cannot see the ChatGPT composer or when login/UI state blocks sending.

When the Codex in-app Browser plugin is available in the active thread, Codex may use that official browser-control channel directly for the external review. The repository CLI still keeps `--transport uia` as the repeatable local Python route because MCP browser calls are not invoked from `scripts/pro_review_cycle.py`.

## Identity And Integrity Contract

Every generated prompt asks ChatGPT Pro to start with:

```text
ROUND_ID: <round-id>
NONCE: <nonce>
SCOPE_REVISADO: <scope>
```

And to finish with:

```text
END_REVIEW: <nonce>
```

Each prompt also includes a `FILES_INCLUDED` block. ChatGPT Pro must review only that scope and must request a follow-up packet when more files are needed.

The global supervisor also requires `PACKET_SHA256` in the Pro answer and verifies it against the packet snapshot. `ingest` and `verify` require those exact markers in the expected positions. This prevents Codex from accepting the copied prompt, an old answer, a partial streaming answer, a response from a different round, or a response for the wrong scope. The prompt, response, backlog, packet manifest, copied-file hashes, and diff hashes are stored in `round.json` and `packet/manifest.json`; prompt writes, response writes, backlog writes, and manifest writes are atomic. Clipboard ingestion validates the response in memory before writing `response.md`.

If a copied ChatGPT answer includes UI text before the response, ingestion trims only up to the last exact `ROUND_ID` marker for that same round, then still validates the nonce, final `END_REVIEW`, required sections, and prompt hash. This recovers from browser copy noise without accepting stale or mismatched responses.

## Completion Standard For A Review Round

A round is complete only when:

- local validation has run before the prompt is created;
- `prompt.md` reflects the current commit or dirty state for the selected scope;
- `round.json` exists and records the nonce, transport, Git head/status, selected scope, response scope, included files, packet snapshot, and prompt hash;
- `packet/manifest.json`, `packet/files/`, and the packet diff exist and match the hashes in `round.json`;
- `response.md` contains the full external answer;
- the response starts with the expected `ROUND_ID`, `NONCE`, and `SCOPE_REVISADO`, and ends with `END_REVIEW`;
- `backlog.md` exactly matches the backlog rendered from `response.md`;
- `round.json` stores matching response and backlog hashes;
- `python scripts/pro_review_cycle.py verify <round-id>` passes;
- the next Codex change references the round id in its reasoning or commit message.

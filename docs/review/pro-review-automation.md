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

## Commands

Run a review round through the integrated browser panel:

```powershell
python scripts/pro_review_cycle.py run --transport uia --focus "Revisa los cambios recientes y dime el siguiente P0 antes del render-model compiler."
```

This creates the round, finds the ChatGPT composer in the Codex side browser, pastes the prompt, sends it, waits for a review-shaped response, writes `response.md`, and regenerates `backlog.md`.

Create a review round without sending it:

```powershell
python scripts/pro_review_cycle.py create --copy --focus "Revisa los cambios recientes y dime el siguiente P0 antes del render-model compiler."
```

This writes:

- `docs/review/pro-rounds/<round-id>/prompt.md`
- `docs/review/pro-rounds/<round-id>/response.md`
- `docs/review/pro-rounds/<round-id>/backlog.md`
- `docs/review/pro-rounds/<round-id>/round.json`

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

- `prompt.md`: complete review packet, including Git state, review docs, limitations, architecture map, validation log, and checklist.
- `response.md`: raw ChatGPT Pro answer.
- `backlog.md`: extracted `P0`, `P1`, `P2`, plan, and tests from the response.
- `round.json`: round state, nonce, transport, Git head/status, and prompt/response hashes.

Keep these under `docs/review/pro-rounds/` because they are review evidence, not reusable skill references. Rounds are local by default and ignored by Git because they may contain transient external responses; commit a completed round only if it is intentionally needed as public review evidence.

## Browser Adapter Boundary

The intended automated route is:

```powershell
python scripts/pro_review_cycle.py run --transport uia --timeout-seconds 1800
```

It performs:

1. Create a round.
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
```

And to finish with:

```text
END_REVIEW: <nonce>
```

`ingest` and `verify` require those exact markers in the expected positions. This prevents Codex from accepting the copied prompt, an old answer, a partial streaming answer, or a response from a different round. The prompt, response, and backlog hashes are stored in `round.json`; prompt writes, response writes, backlog writes, and manifest writes are atomic. Clipboard ingestion validates the response in memory before writing `response.md`.

## Completion Standard For A Review Round

A round is complete only when:

- local validation has run before the prompt is created;
- `prompt.md` reflects the current commit or dirty state;
- `round.json` exists and records the nonce, transport, Git head/status, and prompt hash;
- `response.md` contains the full external answer;
- the response starts with the expected `ROUND_ID` and `NONCE` and ends with `END_REVIEW`;
- `backlog.md` exactly matches the backlog rendered from `response.md`;
- `round.json` stores matching response and backlog hashes;
- `python scripts/pro_review_cycle.py verify <round-id>` passes;
- the next Codex change references the round id in its reasoning or commit message.

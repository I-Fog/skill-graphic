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

The transport layer can be manual clipboard, browser automation, or a future API-backed adapter. The repo contract lives in `scripts/pro_review_cycle.py`; browser control is intentionally outside the math validators and renderers.

## Commands

Create a review round:

```powershell
python scripts/pro_review_cycle.py create --copy --focus "Revisa los cambios recientes y dime el siguiente P0 antes del render-model compiler."
```

This writes:

- `docs/review/pro-rounds/<round-id>/prompt.md`
- `docs/review/pro-rounds/<round-id>/response.md`
- `docs/review/pro-rounds/<round-id>/backlog.md`

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

Preview the prompt without writing files:

```powershell
python scripts/pro_review_cycle.py create --dry-run
```

## Round Artifacts

- `prompt.md`: complete review packet, including Git state, review docs, limitations, architecture map, validation log, and checklist.
- `response.md`: raw ChatGPT Pro answer.
- `backlog.md`: extracted `P0`, `P1`, `P2`, plan, and tests from the response.

Keep these under `docs/review/pro-rounds/` because they are review evidence, not reusable skill references. Rounds are local by default and ignored by Git because they may contain transient external responses; commit a completed round only if it is intentionally needed as public review evidence.

## Browser Adapter Boundary

The intended fully automated route is:

1. Create a round with `scripts/pro_review_cycle.py create`.
2. Open the active ChatGPT Pro conversation.
3. Send `prompt.md`.
4. Wait for generation to finish.
5. Save the answer to `response.md`.
6. Run `scripts/pro_review_cycle.py ingest <round-id>`.

Current fallback: clipboard transport. It preserves the same artifacts and lets Codex continue the loop even when browser automation is unavailable or blocked by login/UI state.

## Completion Standard For A Review Round

A round is complete only when:

- local validation has run before the prompt is created;
- `prompt.md` reflects the current commit or dirty state;
- `response.md` contains the full external answer;
- `backlog.md` has been regenerated from that answer;
- the next Codex change references the round id in its reasoning or commit message.

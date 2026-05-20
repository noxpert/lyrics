# Copilot / AI Assistant Instructions — Lyrics App

This file is the canonical AI-tooling guide for this repo. GitHub Copilot reads
it from `.github/copilot-instructions.md`; recent JetBrains AI Assistant builds
also pick it up. Other AI tools (Claude Code, Cursor, Aider) should be pointed
here too — keep this file as the single source of truth.

## What this app is

A **local, single-user** lyrics viewer/editor for macOS. Runs entirely offline.
No auth, no multi-user concerns, no network calls. The whole thing is launched
by double-clicking `Launch Lyrics.command`, which spins up a FastAPI server on
`http://localhost:8765` and opens the browser.

## Architecture (deliberately small)

```
main.py              FastAPI app + SQLite access + uvicorn entrypoint
static/index.html    The entire SPA: HTML + CSS + vanilla JS, one file
lyrics.db            SQLite, created on first run, user data — gitignored
Launch Lyrics.command  Bash launcher: creates .venv, installs deps, runs main.py
requirements.txt     fastapi, uvicorn[standard]
```

- **One table**: `songs(id, title UNIQUE COLLATE NOCASE, lyrics_json, created_at, updated_at)`.
  `lyrics_json` is a JSON-encoded array of column strings. Read it with
  `json.loads`, write with `json.dumps`. Column count is implicit (array length)
  and currently capped at 3 by the API validator; raise that cap in
  `validate_lyrics` to add more.
- **REST endpoints** under `/api/songs` (list/get/create/update/delete). All other
  paths fall through to `index.html` so the SPA can own routing.
- **No build step.** No bundler, no framework, no npm. Edit `index.html` directly.
- **No tests yet.** If adding behavior worth testing, prefer `pytest` against the
  FastAPI app via `httpx.AsyncClient` / `TestClient`. Keep tests offline.

## Conventions

- Match the existing style: small functions, no abstractions added speculatively.
- Frontend uses vanilla JS with global functions invoked from inline `onclick`.
  Keep it that way — don't introduce a framework or module system.
- CSS lives in a `<style>` block at the top of `index.html`, organized by section
  comments (`/* ── Topbar ── */`, etc.). Use the existing CSS custom properties
  in `:root` rather than hardcoding colors or fonts.
- Fonts are Google Fonts (Playfair Display for display, DM Sans for UI, DM Mono
  for the lyrics textarea). Don't add more font families without reason.
- Keep `main.py` boring: stdlib `sqlite3`, no ORM, no migration framework. If a
  schema change is needed, add an idempotent `ALTER TABLE` in `init_db()`.

## What NOT to do

- Don't add auth, accounts, or any network egress.
- Don't add a JS build system or move `index.html` into a framework.
- Don't bypass `json.loads`/`json.dumps` when touching `lyrics_json` — raw
  string concatenation will corrupt the data shape.
- Don't ignore `lyrics.db` casually — it holds the user's data. Never delete or
  overwrite it as part of a change.
- Don't commit `.venv/`, `.server.pid`, `lyrics.db`, or `.idea/`.

## Running locally

```bash
./Launch\ Lyrics.command          # full path: creates venv, runs server, opens browser
# or, in an already-activated venv:
python3 main.py
```

Server logs to the Terminal window. Stop with Ctrl-C or by closing the window.

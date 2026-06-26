# Contributing

FlowPilot is still at an early stage. Small, focused changes are easier to review than large
rewrites. If a change affects how workflows are stored or executed, open an issue first so the
file format does not drift without discussion.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

The web UI lives in `web/` (Vite + React + TypeScript). For day-to-day UI work, run the engine and
the Vite dev server side by side — the dev server proxies to the engine on `127.0.0.1:8765`:

```powershell
python -m flowpilot.engine      # terminal 1: engine + API
cd web; npm install; npm run dev # terminal 2: http://localhost:5173
```

To run the whole thing the way a user would, use `.\start.ps1` from the repo root.

Before opening a pull request, run:

```powershell
python -m ruff check src tests
python -m pytest -q
cd web; npm run build           # type-check + build the UI
```

Tests that control the real mouse or keyboard do not belong in the automated suite. Use fakes at
that boundary and describe any manual checks in the pull request.

## Pull requests

- Keep one concern per pull request.
- Add tests for parsing, matching, and execution behavior.
- Update the README only when the documented behavior is available.
- Do not commit captured screens, account details, game assets, or other material you cannot
  redistribute.


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

Before opening a pull request, run:

```powershell
python -m ruff check src tests
python -m pytest -q
```

Tests that control the real mouse or keyboard do not belong in the automated suite. Use fakes at
that boundary and describe any manual checks in the pull request.

## Pull requests

- Keep one concern per pull request.
- Add tests for parsing, matching, and execution behavior.
- Update the README only when the documented behavior is available.
- Do not commit captured screens, account details, game assets, or other material you cannot
  redistribute.


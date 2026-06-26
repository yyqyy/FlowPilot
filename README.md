# FlowPilot

FlowPilot is an open-source, **local** visual automation tool — like a Logitech-style macro manager,
but with a blueprint-style node editor. You wire up tasks in the browser UI; a local Python engine
runs them against the real desktop and listens for **global hotkeys** to start/stop them.

> Status: early MVP. The product is a **local engine + web UI**: build node-graph tasks, bind
> hotkeys, and run them. Image targets are matched on screen (no fixed coordinates), so the same
> task works on any machine.

## How it works

- **Web UI** (`web/`) — a node editor: find-and-click images, find-and-type, key presses, delays,
  launch apps, and a condition node that branches on what's on screen.
- **Local engine** (`src/flowpilot/engine/`) — runs tasks with OpenCV template matching + direct
  input control, persists them locally, and registers global start/stop hotkeys.
- The browser only edits and controls; the engine does the automation. Nothing is "exported" — your
  tasks live in the engine and run there.

## Run it (Windows)

One command — sets everything up on first run, then starts the engine and opens the browser:

```powershell
.\start.ps1
```

`start.ps1` creates the virtual environment, installs dependencies, builds the web UI on first run,
and launches the engine at **http://127.0.0.1:8765**. Use `.\start.ps1 -Rebuild` after changing the
web UI. Press `Ctrl+C` in the terminal to stop.

<details>
<summary>Manual steps (or non-Windows)</summary>

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd web; npm install; npm run build; cd ..   # build the UI once
flowpilot-studio                            # serves UI + engine at http://127.0.0.1:8765
```

</details>

Build a task, optionally bind a start hotkey, and press it anywhere. Each task runs **once /
multiple times / loop**; pressing the start hotkey again restarts it; the stop hotkey (or moving the
mouse into a screen corner) aborts it. See [web/README.md](web/README.md) for the node reference.

> Global hotkeys may require running the terminal as Administrator on some systems. The toolbar
> shows whether hotkey listening is active; you can always run tasks from the ▶ button.

## Why FlowPilot?

Many automation tools are either code-only or tied to fixed pixel coordinates that break on a
different screen. FlowPilot makes screen-aware automation visual and editable, and targets images
instead of coordinates so tasks are portable across machines.

## Safety and responsible use

Use FlowPilot only on software, accounts, and devices you own or are authorized to automate.
Do not use it to bypass anti-cheat systems, CAPTCHAs, access controls, rate limits, or a service's
rules. A stop hotkey and the PyAutoGUI fail-safe (slam the mouse to a corner) are core requirements.

## Development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
flowpilot-studio
```

Run tests with `pytest`.

Contribution notes are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

See [ROADMAP.md](ROADMAP.md). Contributions and real-world, permission-safe workflow examples
are welcome.

## License

MIT

# FlowPilot

FlowPilot is an open-source visual desktop automation studio. Build reusable workflows by
dragging nodes, connecting them, and configuring actions such as screenshot matching, mouse
clicks, text input, random delays, conditions, and loops.

> Status: early MVP. The editor and screen matching work, but graph connections and the property
> inspector are still under development. Workflows run in **dry-run mode by default**.

## Why FlowPilot?

Many automation tools are either code-only or tied to fixed coordinates. FlowPilot aims to make
screen-aware automation understandable and editable by non-programmers while keeping workflows
portable and reviewable as JSON files.

## Current build

- Drag nodes around an infinite canvas.
- Capture a screen region and create a template node from it.
- Match a template on the desktop with OpenCV and report its coordinates and confidence.
- Run a sequential workflow in dry-run mode.
- Execute fixed-position clicks, matched-image clicks, and text input when dry-run is disabled.
- Add fixed or randomized delays.

The capture overlay currently uses the primary display. Multi-monitor capture is tracked for a
later milestone.

## Try it

Start FlowPilot, select **Capture template**, and drag around a small target on the screen. The
captured image is stored under `assets/templates` and a configured image node is added to the
canvas. Use **Test image** to check whether a saved template can be found on the current desktop.

## Safety and responsible use

Use FlowPilot only on software, accounts, and devices you own or are authorized to automate.
Do not use it to bypass anti-cheat systems, CAPTCHAs, access controls, rate limits, or a service's
rules. An emergency stop and dry-run mode are core product requirements.

## Development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
flowpilot
```

Run tests with `pytest`.

Contribution notes are in [CONTRIBUTING.md](CONTRIBUTING.md).

## Roadmap

See [ROADMAP.md](ROADMAP.md). Contributions and real-world, permission-safe workflow examples
are welcome.

## License

MIT

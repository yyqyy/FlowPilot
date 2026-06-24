# FlowPilot

FlowPilot is an open-source visual desktop automation studio. Build reusable workflows by
dragging nodes, connecting them, and configuring actions such as screenshot matching, mouse
clicks, text input, random delays, conditions, and loops.

> Status: early MVP. Workflows run in **dry-run mode by default** so a new graph cannot take
> control of the mouse or keyboard unexpectedly.

## Why FlowPilot?

Many automation tools are either code-only or tied to fixed coordinates. FlowPilot aims to make
screen-aware automation understandable and editable by non-programmers while keeping workflows
portable and reviewable as JSON files.

## Planned MVP nodes

- Start and Stop
- Capture region and find image with OpenCV
- Click image or fixed position
- Type text and press hotkeys
- Fixed or randomized delay
- Condition, loop, and variable nodes

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

## Roadmap

See [ROADMAP.md](ROADMAP.md). Contributions and real-world, permission-safe workflow examples
are welcome.

## License

MIT


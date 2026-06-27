# FlowPilot Studio (web UI)

The visual node editor for FlowPilot automation tasks. It is the front-end of a **local tool**: you
build node graphs here — wiring nodes with **execution ports** (run order) and **data ports** (typed
values) — and the local Python engine runs them against the real desktop: find images and
click/type/swipe at them, branch on what's on screen, launch apps, and wait. Tasks start on demand
or via a **global hotkey**.

This UI only edits and controls; the engine (in `src/flowpilot/engine`) does the automation and
listens for hotkeys. There is no "export script" — tasks live in the engine and run there.

## Run it (with the engine)

From the repo root, start the engine, which serves this UI and the API:

```powershell
pip install -e ".[dev]"
flowpilot-studio          # opens http://127.0.0.1:8765
```

## Develop the UI alone

```powershell
cd web
npm install
npm run dev      # http://localhost:5173, talks to the engine on 127.0.0.1:8765
npm run build    # type-check + production build into dist/ (served by the engine)
```

## Stack

- Vite + React + TypeScript, [@xyflow/react](https://reactflow.dev/) node canvas
- zustand state synced to the engine's REST API; Tailwind styling

## Node types

| Node | What the engine does |
| --- | --- |
| 找图点击 find_click | Locate a template, click its center (left/right/double + offset); 成功/失败 outputs + 找到 boolean |
| 找图输入 find_type | Locate a field, click it, then type text (or a string from a data wire) |
| 输入文本 type_text | Type into the focused window |
| 按键 key_press | Press a key or combo (e.g. ctrl+c) |
| 延迟 delay | Wait a fixed or random time |
| 启动软件 launch_app | Start a program, optionally wait |
| 滑动 swipe | Mark ordered points on a full-screen screenshot and press-drag through them, per-segment duration |
| 看图判断 condition | Branch on whether a template is on screen (真/假) + 找到 boolean |
| 分支 branch | Route execution on a boolean data input (真/假) |
| 重复循环 loop | Repeat the body a fixed number of times |
| 条件循环 loop_while | Repeat while a boolean wire (or image) condition holds |
| 获取变量 / 设置变量 var_get / var_set | Read or write a typed variable (布尔 / 文本 / 坐标点) via data wires |

White square ports are execution wires (run order); coloured round ports are data wires (typed
values). Declare variables in the side panel and drag their Get/Set nodes onto the canvas.

Target images are picked or dragged onto the canvas and embedded (base64); the engine decodes and
matches them in memory, so the same task works on any machine — no fixed coordinates.

## Triggers

Each task runs **once / multiple times / loop**, can bind a **start hotkey** and a **stop hotkey**,
and pressing the start hotkey again restarts the task from the beginning.

## Safety

Only automate software, accounts, and devices you own or are authorized to use. Do not use it to
bypass anti-cheat, CAPTCHAs, access controls, or a service's rules. Move the mouse into a screen
corner (PyAutoGUI fail-safe) or press the stop hotkey to abort.

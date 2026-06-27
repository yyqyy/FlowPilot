# FlowPilot

**Language / 语言:** [English](#english) · [中文](#中文)

> An open-source, **local-first** visual desktop automation tool. You wire up tasks in the browser
> with a node graph — **execution wires** decide the order and **data wires** carry typed values —
> and a local Python engine runs them against the real desktop, listening for **global hotkeys** to
> start and stop them.
>
> 开源、**纯本地**的可视化桌面自动化工具。在浏览器里用节点图搭建任务 —— **执行线**决定运行顺序、
> **数据线**传递带类型的值 —— 本地的 Python 引擎在真实桌面上执行，并监听**全局快捷键**启动/停止。

📖 **New here? Follow the step-by-step guide → [DEPLOYMENT.md](DEPLOYMENT.md)**
（第一次使用？请按照保姆级教程操作 → [DEPLOYMENT.md](DEPLOYMENT.md)）

---

## English

FlowPilot is a **local engine + web UI**: build node-graph tasks in the browser, bind hotkeys, and
run them against your own desktop. Image targets are matched on screen with OpenCV (no fixed
coordinates), so the same task works on any machine.

> Status: early MVP.

### How it works

- **Web UI** (`web/`) — a node editor: find-and-click images, find-and-type, swipe gestures, key
  presses, delays, launch apps, conditions/branches, loops, and typed variables wired together with
  execution and data ports.
- **Local engine** (`src/flowpilot/engine/`) — runs tasks with OpenCV template matching + direct
  input control, persists them locally, and registers global start/stop hotkeys.
- The browser only edits and controls; the engine does the automation. Nothing is "exported" — your
  tasks live in the engine and run there.

### Quick start (Windows)

**Prerequisites:** Windows 10/11, [Python 3.11+](https://www.python.org/downloads/) (tested on
3.13), and [Node.js 18+](https://nodejs.org/) (tested on 22). Make sure both are on your `PATH`.

One command — it sets everything up on first run, then starts the engine and opens the browser:

```powershell
.\start.ps1
```

If PowerShell refuses to run the script (`running scripts is disabled`), use:

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

`start.ps1` creates the virtual environment, installs dependencies, builds the web UI on first run,
and launches the engine at **http://127.0.0.1:8765**. Use `.\start.ps1 -Rebuild` after changing the
web UI. Press `Ctrl+C` in the terminal to stop.

> 👉 If anything goes wrong (Python/Node not found, port in use, hotkeys not firing), the
> **[full deployment guide](DEPLOYMENT.md)** has prerequisites, manual steps, and troubleshooting
> for every common error.

### Node types

| Node | What the engine does |
| --- | --- |
| 开始 / 结束 `start` / `stop` | Entry and exit of the graph |
| 找图点击 `find_click` | Locate a template on screen, click its center (left/right/double + offset). Has **成功 / 失败** execution outputs and a **找到** boolean data output |
| 找图输入 `find_type` | Locate a field, click it, then type text (or a string fed in by a data wire) |
| 输入文本 `type_text` | Type into the focused window |
| 按键 `key_press` | Press a key or combo (e.g. `ctrl+c`) |
| 延迟 `delay` | Wait a fixed or random time |
| 启动软件 `launch_app` | Start a program, optionally wait |
| 滑动 `swipe` | Mark ordered points on a full-screen screenshot, then press-drag through them 1→2→3 with a per-segment duration |
| 看图判断 `condition` | Branch on whether a template is on screen (真/假) and expose a **找到** boolean output |
| 分支 `branch` | Route execution on a boolean data input (真/假) |
| 重复循环 `loop` | Repeat the body a fixed number of times |
| 条件循环 `loop_while` | Repeat the body while a boolean wire (or an image) condition holds |
| 获取变量 / 设置变量 `var_get` / `var_set` | Read or write a typed variable via data wires |

**Two kinds of wires.** White **square ports** are *execution wires* — they decide what runs next.
Coloured **round ports** are *data wires* — they pass typed values between nodes. A node like
找图点击 routes flow through **成功 / 失败** and also offers its result as a **找到** boolean that you
can feed into a variable or a 分支.

**Variables.** Declare variables in the side panel with a type — **布尔 / 文本 / 坐标点** — then drag
their **获取 / 设置** nodes onto the canvas and connect them with data wires.

Target images are picked or dragged onto the canvas and embedded (base64); the engine decodes and
matches them in memory, so the same task works on any machine — no fixed coordinates.

### Triggers

Each task runs **once / multiple times / loop**, can bind a **start hotkey** and a **stop hotkey**,
and pressing the start hotkey again restarts the task from the beginning. The stop hotkey — or
slamming the mouse into a screen corner (PyAutoGUI fail-safe) — aborts it.

> Global hotkeys may require running the terminal as **Administrator** on some systems. The toolbar
> shows whether hotkey listening is active; you can always run tasks from the ▶ button.

### Why FlowPilot?

Many automation tools are either code-only or tied to fixed pixel coordinates that break on a
different screen. FlowPilot makes screen-aware automation visual and editable, and targets images
instead of coordinates so tasks are portable across machines.

### Safety and responsible use

Use FlowPilot only on software, accounts, and devices you own or are authorized to automate.
Do not use it to bypass anti-cheat systems, CAPTCHAs, access controls, rate limits, or a service's
rules. A stop hotkey and the PyAutoGUI fail-safe (slam the mouse to a corner) are core requirements.

### Development

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
flowpilot-studio
```

Run tests with `pytest`. Contribution notes are in [CONTRIBUTING.md](CONTRIBUTING.md); the roadmap is
in [ROADMAP.md](ROADMAP.md).

### License

MIT

---

## 中文

FlowPilot 是一个**本地引擎 + 网页界面**的组合：你在浏览器里搭建节点流程、绑定快捷键，然后在
自己的桌面上运行它。图像目标由 OpenCV 在屏幕上实时匹配（不依赖固定坐标），所以同一个任务在任何
机器上都能用。

> 状态：早期 MVP。

### 工作原理

- **网页界面**（`web/`）—— 节点编辑器：找图点击、找图输入、滑动、按键、延迟、启动软件、判断、分支、
  循环、带类型的变量，用执行口与数据口连接成流程。
- **本地引擎**（`src/flowpilot/engine/`）—— 用 OpenCV 模板匹配 + 直接输入控制来执行任务，本地持久化，
  并注册全局启动/停止快捷键。
- 浏览器只负责编辑和控制，引擎负责真正的自动化。没有"导出"这一步 —— 任务就保存在引擎里、在那里运行。

### 快速开始（Windows）

**前置条件：** Windows 10/11、[Python 3.11+](https://www.python.org/downloads/)（在 3.13 上测试过）、
[Node.js 18+](https://nodejs.org/)（在 22 上测试过）。请确认两者都已加入 `PATH` 环境变量。

一条命令 —— 首次运行会自动完成所有准备工作，然后启动引擎并打开浏览器：

```powershell
.\start.ps1
```

如果 PowerShell 拒绝运行脚本（提示 `running scripts is disabled` / 禁止运行脚本），改用：

```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

`start.ps1` 会创建虚拟环境、安装依赖、首次运行时构建网页界面，并在 **http://127.0.0.1:8765**
启动引擎。改动网页界面后用 `.\start.ps1 -Rebuild` 重新构建。在终端里按 `Ctrl+C` 停止。

> 👉 如果遇到任何问题（找不到 Python/Node、端口被占用、快捷键没反应），
> **[完整部署教程](DEPLOYMENT.md)** 里有每一步的前置条件、手动步骤和常见报错排查。

### 节点类型

| 节点 | 引擎做的事 |
| --- | --- |
| 开始 / 结束 `start` / `stop` | 流程的起点与终点 |
| 找图点击 `find_click` | 在屏幕上找到模板图，点击其中心（左键/右键/双击 + 偏移）；有 **成功 / 失败** 执行口和 **找到** 布尔数据口 |
| 找图输入 `find_type` | 找到输入框，点击它，再输入文字（也可由数据线传入文本） |
| 输入文本 `type_text` | 向当前焦点窗口输入文字 |
| 按键 `key_press` | 按下某个键或组合键（如 `ctrl+c`） |
| 延迟 `delay` | 固定或随机等待一段时间 |
| 启动软件 `launch_app` | 启动一个程序，可选择是否等待 |
| 滑动 `swipe` | 在整屏截图上按 1→2→3 顺序标点，按住依次滑到末点松开，每段可单独设时长 |
| 看图判断 `condition` | 根据某模板是否在屏幕上分支（真/假），并提供 **找到** 布尔数据口 |
| 分支 `branch` | 按输入的布尔数据线分流（真/假） |
| 重复循环 `loop` | 把循环体重复固定次数 |
| 条件循环 `loop_while` | 当布尔数据线（或图片）条件成立时重复循环体 |
| 获取变量 / 设置变量 `var_get` / `var_set` | 通过数据线读取或写入一个带类型的变量 |

**两种连线。** 白色**方口**是*执行线* —— 决定下一步运行谁；彩色**圆口**是*数据线* —— 在节点间传递
带类型的值。像找图点击这样的节点会从 **成功 / 失败** 分流，同时把结果作为 **找到** 布尔值输出，可接到
变量或 分支 节点。

**变量。** 在侧边面板新建变量并选择类型 —— **布尔 / 文本 / 坐标点** —— 然后把它的 **获取 / 设置**
节点拖到画布，用数据线连接。

目标图片通过选择或拖拽放到画布上并以 base64 内嵌；引擎在内存里解码并匹配，所以同一个任务在任何机器上
都能用 —— 没有固定坐标。

### 触发方式

每个任务可以**运行一次 / 多次 / 循环**，可绑定**启动快捷键**和**停止快捷键**；再次按下启动快捷键
会从头重新开始。停止快捷键 —— 或者把鼠标猛地甩到屏幕角落（PyAutoGUI 安全急停）—— 都能中止任务。

> 在某些系统上，全局快捷键可能需要以**管理员身份**运行终端。工具栏会显示快捷键监听是否生效；
> 你随时都可以用 ▶ 按钮手动运行任务。

### 为什么用 FlowPilot？

很多自动化工具要么只能写代码，要么绑死在固定像素坐标上，一换屏幕就失效。FlowPilot 让"看得懂屏幕"的
自动化变得可视化、可编辑，并且以图像而非坐标为目标，所以任务能在不同机器之间通用。

### 安全与负责任地使用

只在你拥有或被授权自动化的软件、账号和设备上使用 FlowPilot。不要用它绕过反作弊系统、验证码、访问控制、
速率限制或服务条款。停止快捷键和 PyAutoGUI 安全急停（把鼠标甩到角落）是核心保障，请务必保留。

### 参与开发

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
flowpilot-studio
```

用 `pytest` 运行测试。贡献说明见 [CONTRIBUTING.md](CONTRIBUTING.md)，路线图见 [ROADMAP.md](ROADMAP.md)。

### 许可证

MIT

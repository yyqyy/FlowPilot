# Deployment & Usage Guide / 部署与使用教程

A step-by-step, **foolproof** guide. Follow it top to bottom and FlowPilot will run on a clean
Windows machine without "command not found" or "won't start" errors.

一份**保姆级**的分步教程。从头跟着做，FlowPilot 就能在一台干净的 Windows 机器上跑起来，
不会出现"找不到命令""启动不了"之类的问题。

**Language / 语言:** [English](#english-guide) · [中文](#中文教程)

---

## English Guide

### 1. What you need first (prerequisites)

| Tool | Minimum | Tested | How to check |
| --- | --- | --- | --- |
| Windows | 10 / 11 | 11 | — |
| Python | 3.11 | 3.13.5 | `python --version` |
| Node.js + npm | Node 18 | Node 22.14 / npm 10.9 | `node --version` and `npm --version` |

**Install Python** from <https://www.python.org/downloads/>. On the first installer screen, **tick
"Add python.exe to PATH"** — this is the single most common cause of "python is not recognized".

**Install Node.js (LTS)** from <https://nodejs.org/>. The installer adds `node` and `npm` to PATH
automatically; just restart your terminal afterwards.

> After installing, **open a new PowerShell window** so it picks up the updated PATH, then verify:
>
> ```powershell
> python --version    # should print Python 3.11+  
> node --version      # should print v18+  
> npm --version
> ```
>
> If any command prints nothing or an error, fix PATH before continuing (see
> [Troubleshooting](#7-troubleshooting)).

### 2. Get the code

```powershell
git clone https://github.com/yyqyy/FlowPilot.git
cd FlowPilot
```

No Git? Download the ZIP from the GitHub page (**Code → Download ZIP**), extract it, and `cd` into
the extracted folder.

### 3. Run it — the one-command way (recommended)

From the repository root:

```powershell
.\start.ps1
```

That single script will, in order:

1. Create a Python virtual environment in `.venv\`
2. Install the Python engine and its dependencies
3. Build the web UI (`web\dist\`) — **the first build is slow (a few minutes); this is normal**
4. Start the engine and open your browser at **http://127.0.0.1:8765**

When you see `FlowPilot 引擎已启动：http://127.0.0.1:8765` and the browser opens, you're done.

**If PowerShell blocks the script** with `... start.ps1 cannot be loaded because running scripts is
disabled on this system`, that's Windows' default execution policy. Pick one:

```powershell
# One-off (does not change any system setting):
powershell -ExecutionPolicy Bypass -File .\start.ps1

# Or allow local scripts for your user permanently (run once):
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**To stop the engine:** press `Ctrl+C` in the terminal.

**After you change the web UI** and want the new build served:

```powershell
.\start.ps1 -Rebuild
```

### 4. Run it — the manual way (if you don't want the script)

Do this if you're on a restricted machine or prefer to see each step:

```powershell
# 1) create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) install the engine (editable) + dev tools
pip install -e ".[dev]"

# 3) build the web UI once
cd web
npm install
npm run build
cd ..

# 4) start the engine (serves the UI + API at http://127.0.0.1:8765)
flowpilot-studio
```

`flowpilot-studio` and `python -m flowpilot.engine` are equivalent entry points.

### 5. First-run checklist (make sure it actually works)

1. Browser opens at **http://127.0.0.1:8765** showing the FlowPilot editor.
2. Click **+ New task** — an empty graph with a 开始 (Start) and 结束 (Stop) node appears.
3. Drag a node from the left palette onto the canvas, connect 开始 → your node → 结束.
4. Press the ▶ (Run) button. The bottom log shows each step.
5. Optional: bind a **start hotkey** in the inspector and press it anywhere on the desktop.

If hotkeys don't fire, see [Global hotkeys](#6-global-hotkeys-administrator) below.

### 6. Global hotkeys (Administrator)

FlowPilot uses the `keyboard` library for global hotkeys. On some Windows setups this needs elevated
privileges. If the toolbar shows hotkeys are **inactive**, close the terminal and reopen
**PowerShell as Administrator**, then run `.\start.ps1` again.

You can always run tasks from the ▶ button even without working hotkeys.

### 7. Where your tasks are stored

Tasks are auto-saved as one JSON file each — **no manual export**:

```
%APPDATA%\FlowPilot\tasks\
```

(Open it by pasting `%APPDATA%\FlowPilot\tasks` into the Explorer address bar.) This folder lives in
your user profile, **not** in the repository, so it is never committed and is safe from
`git clean`/`git pull`. Back up that folder to keep your tasks.

### 8. Troubleshooting

| Symptom | Cause & fix |
| --- | --- |
| `python is not recognized` | Python not on PATH. Reinstall with **"Add python.exe to PATH"** ticked, or add it manually, then open a **new** terminal. |
| `npm` / `node is not recognized` | Node.js not installed or terminal not restarted. Install Node LTS, open a new terminal. |
| `running scripts is disabled on this system` | Execution policy. Use `powershell -ExecutionPolicy Bypass -File .\start.ps1` or `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| Browser doesn't open | Open **http://127.0.0.1:8765** manually. The auto-open is best-effort. |
| `[Errno 10048] ... address already in use` (port 8765) | Another instance is running. Close it, or find it with `Get-NetTCPConnection -LocalPort 8765` and stop that process. |
| `npm run build` fails | Delete `web\node_modules` and `web\package-lock.json`, run `npm install` again. Ensure Node ≥ 18. |
| Web page says "网页界面尚未构建" | The UI isn't built. Run `.\start.ps1 -Rebuild`, or `cd web; npm install; npm run build`. |
| Hotkeys don't trigger | Run the terminal **as Administrator** (see §6). Use the ▶ button meanwhile. |
| Engine starts but clicks/types do nothing | The target image isn't matched on screen. Re-capture the template at the current resolution/scale. |
| Antivirus blocks input control | `pyautogui`/`keyboard` simulate input. Allow FlowPilot/Python in your AV, or run on a machine you control. |

### 9. Updating to a newer version

```powershell
git pull
.\start.ps1 -Rebuild   # rebuilds the UI and reinstalls anything new
```

Your tasks in `%APPDATA%\FlowPilot\tasks\` are untouched by updates.

---

## 中文教程

### 1. 先准备好这些（前置条件）

| 工具 | 最低版本 | 已测试版本 | 怎么检查 |
| --- | --- | --- | --- |
| Windows | 10 / 11 | 11 | —— |
| Python | 3.11 | 3.13.5 | `python --version` |
| Node.js + npm | Node 18 | Node 22.14 / npm 10.9 | `node --version` 和 `npm --version` |

**安装 Python**：到 <https://www.python.org/downloads/> 下载。安装第一屏一定要**勾选
"Add python.exe to PATH"** —— 不勾选是"找不到 python 命令"最常见的原因。

**安装 Node.js（LTS 版）**：到 <https://nodejs.org/> 下载。安装程序会自动把 `node` 和 `npm`
加入 PATH，装完**重启一下终端**即可。

> 装完后**新开一个 PowerShell 窗口**（让它读到更新后的 PATH），然后验证：
>
> ```powershell
> python --version    # 应显示 Python 3.11 或更高
> node --version      # 应显示 v18 或更高
> npm --version
> ```
>
> 如果某条命令没有输出或报错，先把 PATH 修好再继续（见[常见问题排查](#9-常见问题排查)）。

### 2. 获取代码

```powershell
git clone https://github.com/yyqyy/FlowPilot.git
cd FlowPilot
```

没有 Git？在 GitHub 页面点 **Code → Download ZIP** 下载压缩包，解压后用 `cd` 进入解压出来的文件夹。

### 3. 启动 —— 一键方式（推荐）

在仓库根目录执行：

```powershell
.\start.ps1
```

这一个脚本会依次完成：

1. 在 `.venv\` 里创建 Python 虚拟环境
2. 安装 Python 引擎及其依赖
3. 构建网页界面（`web\dist\`）—— **首次构建较慢（几分钟），属于正常现象**
4. 启动引擎，并自动在浏览器打开 **http://127.0.0.1:8765**

当看到 `FlowPilot 引擎已启动：http://127.0.0.1:8765` 且浏览器自动打开，就成功了。

**如果 PowerShell 拦截脚本**，提示 `... start.ps1 cannot be loaded because running scripts is
disabled on this system`（系统禁止运行脚本），这是 Windows 默认的执行策略。任选一种解决：

```powershell
# 临时绕过（不改动任何系统设置）：
powershell -ExecutionPolicy Bypass -File .\start.ps1

# 或者为当前用户永久允许本地脚本（运行一次即可）：
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**停止引擎：** 在终端里按 `Ctrl+C`。

**改动了网页界面**、想让新构建生效：

```powershell
.\start.ps1 -Rebuild
```

### 4. 启动 —— 手动方式（不想用脚本时）

如果机器有限制，或你想看清每一步，就用这种方式：

```powershell
# 1) 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) 安装引擎（可编辑模式）+ 开发工具
pip install -e ".[dev]"

# 3) 构建一次网页界面
cd web
npm install
npm run build
cd ..

# 4) 启动引擎（在 http://127.0.0.1:8765 同时提供界面和 API）
flowpilot-studio
```

`flowpilot-studio` 和 `python -m flowpilot.engine` 是等价的两个启动入口。

### 5. 首次运行自检（确认真的能用）

1. 浏览器打开 **http://127.0.0.1:8765**，显示 FlowPilot 编辑器。
2. 点击 **+ 新建任务** —— 出现只有 开始、结束 两个节点的空流程。
3. 从左侧面板拖一个节点到画布上，连成 开始 → 你的节点 → 结束。
4. 点击 ▶（运行）按钮，底部日志会显示每一步。
5. 可选：在右侧检查器里绑定**启动快捷键**，然后在桌面任意位置按下它。

如果快捷键没反应，见下面的[全局快捷键](#6-全局快捷键管理员权限)。

### 6. 全局快捷键（管理员权限）

FlowPilot 用 `keyboard` 库实现全局快捷键。在某些 Windows 环境下这需要管理员权限。如果工具栏显示
快捷键**未生效**，关闭终端，**以管理员身份重新打开 PowerShell**，再次运行 `.\start.ps1`。

即使快捷键不工作，你也始终可以用 ▶ 按钮手动运行任务。

### 7. 任务保存在哪里

任务会自动保存，每个任务一个 JSON 文件 —— **无需手动导出**：

```
%APPDATA%\FlowPilot\tasks\
```

（把 `%APPDATA%\FlowPilot\tasks` 粘贴到资源管理器地址栏即可打开。）这个文件夹在你的用户目录下，
**不在**仓库里，因此永远不会被提交，也不受 `git clean`/`git pull` 影响。想保留任务就备份这个文件夹。

### 8. 节点速查

| 节点 | 作用 |
| --- | --- |
| 开始 / 结束 | 流程的起点与终点 |
| 找图点击 | 在屏幕上找到模板图，点击中心（左键/右键/双击 + 偏移） |
| 找图输入 | 找到输入框，点击后输入文字 |
| 输入文本 | 向当前焦点窗口输入文字 |
| 按键 | 按下某个键或组合键（如 `ctrl+c`） |
| 延迟 | 固定或随机等待 |
| 启动软件 | 启动程序，可选择是否等待 |
| 判断 | 根据模板是否在屏幕上分支（是/否） |
| 循环 | 把循环体重复固定次数 |
| 条件循环 | 当图像/变量条件成立时重复循环体 |
| 设置变量 / 判断变量 | 写入 / 读取具名布尔变量并分支 |

### 9. 常见问题排查

| 现象 | 原因与解决 |
| --- | --- |
| `python 不是内部或外部命令` / `not recognized` | Python 没进 PATH。重装时勾选 **"Add python.exe to PATH"**，或手动加入，然后**新开**终端。 |
| `npm` / `node 不是命令` | 没装 Node 或没重启终端。装 Node LTS 后新开终端。 |
| `running scripts is disabled on this system` | 执行策略限制。用 `powershell -ExecutionPolicy Bypass -File .\start.ps1`，或 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`。 |
| 浏览器没自动打开 | 手动访问 **http://127.0.0.1:8765**，自动打开只是尽力而为。 |
| `[Errno 10048] ... address already in use`（端口 8765 被占用） | 已有一个实例在运行。关掉它，或用 `Get-NetTCPConnection -LocalPort 8765` 找到进程并结束。 |
| `npm run build` 失败 | 删除 `web\node_modules` 和 `web\package-lock.json`，重新 `npm install`。确认 Node ≥ 18。 |
| 网页显示"网页界面尚未构建" | 界面没构建。运行 `.\start.ps1 -Rebuild`，或 `cd web; npm install; npm run build`。 |
| 快捷键不触发 | 以**管理员身份**运行终端（见 §6）。期间可用 ▶ 按钮。 |
| 引擎启动了但点击/输入没反应 | 屏幕上没匹配到目标图。在当前分辨率/缩放下重新截取模板。 |
| 杀毒软件拦截输入控制 | `pyautogui`/`keyboard` 会模拟输入。在杀毒软件里放行 FlowPilot/Python，或在你自己掌控的机器上运行。 |

### 10. 更新到新版本

```powershell
git pull
.\start.ps1 -Rebuild   # 重新构建界面并安装新增依赖
```

更新不会动 `%APPDATA%\FlowPilot\tasks\` 里的任务。

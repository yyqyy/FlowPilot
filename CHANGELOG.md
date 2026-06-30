# Changelog / 更新日志

All notable changes to FlowPilot are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/).

本文件记录 FlowPilot 的所有重要变更。格式参考 [Keep a Changelog](https://keepachangelog.com/)，
版本号遵循[语义化版本](https://semver.org/)。每次发布请在下方新增一节，并按
**Added 新增 / Changed 变更 / Fixed 修复 / Removed 移除** 分类记录。

## [0.2.1] - 2026-06-30

Find-image actions can now wait for the screen to settle instead of giving up on
the first look. 找图类节点现在可以等画面稳定后再判断，而不是看一眼就放弃。

### Added 新增

- Retry & timeout for `find_click` / `find_type` / `condition`: each find-image node
  has a **查找超时**（seconds to keep looking; `0` keeps the original single-attempt
  behaviour）and a **重试间隔**. If the template isn't on screen yet, the engine keeps
  re-checking every interval until it appears or the timeout passes, then routes to
  **失败 / 假** — so flows survive slow-rendering windows without an extra 延迟 node.
  为 找图点击 / 找图输入 / 看图判断 增加**查找超时**（持续查找的秒数；`0` 表示只找一次、
  与旧行为一致）和**重试间隔**。图片还没出现时，引擎每隔一段时间就重新查找，直到找到或超时
  才走 **失败 / 假** —— 不用再额外加 延迟 节点也能扛住"窗口加载慢"的情况。

## [0.2.0] - 2026-06-29

A node-graph overhaul: execution wires, typed data wires, typed variables, and a swipe gesture node.
节点图大改：执行线、带类型的数据线、带类型的变量，以及全新的滑动手势节点。

### Added 新增

- Execution wires and data wires: every node now has typed input/output ports — white square ports
  for execution order, coloured round ports for values — and connections are validated by type.
  执行线与数据线：每个节点都有带类型的输入/输出端口 —— 白色方口控制执行顺序、彩色圆口传递值 ——
  连线按类型校验。
- `find_click` / `find_type` / `condition` now branch on their own result: **成功 / 失败**
  (or 真/假) execution outputs plus a **找到** boolean data output.
  找图点击 / 找图输入 / 看图判断 现在能按自身结果分流：**成功 / 失败**（或真/假）执行出口，
  外加一个 **找到** 布尔数据出口。
- Typed variables (**布尔 / 文本 / 坐标点**) with a side panel to create, rename, and retype them,
  plus **获取 / 设置** (`var_get` / `var_set`) nodes wired by data lines.
  带类型的变量（**布尔 / 文本 / 坐标点**），侧边面板可新建、改名、改类型，并提供 **获取 / 设置**
  （`var_get` / `var_set`）节点，用数据线连接。
- `branch` node: route execution on a boolean data input (真/假).
  分支（`branch`）节点：按输入的布尔数据线分流（真/假）。
- `swipe` node: upload a full-screen screenshot and lay out an ordered path. Each point is either
  **按图查找** (box a region on the screenshot; it's located on screen at run time, so it tracks
  elements that move) or **固定位置** (a fixed spot). The engine press-drags through the points
  1→2→3 with a per-segment duration, reports **成功 / 失败**, and logs which point couldn't be found.
  滑动（`swipe`）节点：上传整屏截图并排出一条有序路径。每个点可选 **按图查找**（在截图上框出一块，
  运行时在屏幕上找到它，因此能跟随会移动的元素）或 **固定位置**。引擎按住依次 1→2→3 拖动，每段可单独
  设时长，给出 **成功 / 失败** 出口，并记录是哪个点没找到。

### Changed 变更

- Tasks now store pin-aware connections (`source_handle` / `target_handle` / `kind`) and a
  `variables` list; older saved tasks are migrated on load on a best-effort basis.
  任务现在保存带引脚的连线（`source_handle` / `target_handle` / `kind`）和 `variables` 列表；
  旧任务在加载时尽力自动迁移。

### Fixed 修复

- Windows DPI awareness so clicks, drags, and swipes land on target on scaled displays (125% / 150%).
  Windows DPI 感知，在缩放显示（125% / 150%）下点击、拖拽、滑动都能落到正确位置。

### Removed 移除

- `set_var` and `check_var` nodes — replaced by typed variables (`var_get` / `var_set`) and the
  `branch` node.
  移除 设置变量 `set_var`、判断变量 `check_var` 节点 —— 由带类型的变量（`var_get` / `var_set`）
  和 分支 节点取代。

## [0.1.0] - 2026-06-27

First public version: a local engine plus a web node editor.
首个公开版本：本地引擎 + 网页节点编辑器。

### Added 新增

- Local automation engine: node-graph tasks executed against the real desktop with OpenCV
  template matching and direct input control, persisted per-user, with global start/stop hotkeys
  and run **once / multiple times / loop** triggers.
  本地自动化引擎：用 OpenCV 模板匹配 + 直接输入控制在真实桌面上执行节点流程，按用户持久化，
  支持全局启动/停止快捷键，以及**一次 / 多次 / 循环**触发。
- Web node editor (Vite + React) with nodes: `find_click`, `find_type`, `type_text`, `key_press`,
  `delay`, `launch_app`, `condition`, `loop`, `loop_while`, `set_var`, `check_var`.
  网页节点编辑器（Vite + React），节点包括：找图点击、找图输入、输入文本、按键、延迟、启动软件、
  判断、循环、条件循环、设置变量、判断变量。
- Loops, boolean variables, and a per-node delay after screen-affecting actions so matches settle
  before the next step.
  循环、布尔变量，以及在影响屏幕的动作后加入按节点的延迟，让画面稳定后再执行下一步。
- Palette drag-and-drop, click preview, and an inspector for every node type.
  从面板拖拽放置节点、点击预览，以及每种节点的属性检查器。
- One-command Windows launcher `start.ps1` (creates the venv, installs deps, builds the UI, starts
  the engine).
  Windows 一键启动脚本 `start.ps1`（创建虚拟环境、安装依赖、构建界面、启动引擎）。
- Bilingual documentation: `README.md` and a step-by-step `DEPLOYMENT.md` (setup, usage,
  troubleshooting).
  中英双语文档：`README.md` 与保姆级 `DEPLOYMENT.md`（部署、使用、排错）。

### Fixed 修复

- Typing Chinese text reliably, and made the target image optional for `find_type`.
  修复中文文本输入；`find_type` 的目标图片改为可选。

[0.2.1]: https://github.com/yyqyy/FlowPilot/releases/tag/v0.2.1
[0.2.0]: https://github.com/yyqyy/FlowPilot/releases/tag/v0.2.0
[0.1.0]: https://github.com/yyqyy/FlowPilot/releases/tag/v0.1.0

# Changelog / 更新日志

All notable changes to FlowPilot are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/).

本文件记录 FlowPilot 的所有重要变更。格式参考 [Keep a Changelog](https://keepachangelog.com/)，
版本号遵循[语义化版本](https://semver.org/)。每次发布请在下方新增一节，并按
**Added 新增 / Changed 变更 / Fixed 修复 / Removed 移除** 分类记录。

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

[0.1.0]: https://github.com/yyqyy/FlowPilot/releases/tag/v0.1.0

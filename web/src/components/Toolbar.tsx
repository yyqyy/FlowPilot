import { useStore } from '../store'

// The toolbar is intentionally minimal: run/stop and run-status now live next to
// each task in the left list (player-style ▶). Here we keep only branding and the
// current task's name.
export function Toolbar() {
  const settings = useStore((s) => s.settings)
  const updateSettings = useStore((s) => s.updateSettings)

  return (
    <header className="fp-toolbar">
      <div className="fp-brand">
        <span className="fp-brand-mark">✦</span>
        <span className="fp-brand-name">FlowPilot</span>
      </div>

      <input
        className="fp-name-input"
        value={settings.name}
        spellCheck={false}
        onChange={(e) => updateSettings({ name: e.target.value })}
        aria-label="任务名称"
      />

      <div className="fp-toolbar-spacer" />

      <div className="fp-toolbar-hint">在左侧任务列表用 ▶ 启动 / 停止脚本</div>
    </header>
  )
}

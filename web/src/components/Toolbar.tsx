import { OctagonX, Play, Square } from 'lucide-react'

import { useStore } from '../store'

export function Toolbar() {
  const settings = useStore((s) => s.settings)
  const currentId = useStore((s) => s.currentId)
  const running = useStore((s) => s.running)
  const hotkeysAvailable = useStore((s) => s.hotkeysAvailable)
  const updateSettings = useStore((s) => s.updateSettings)
  const runTask = useStore((s) => s.runTask)
  const stopTask = useStore((s) => s.stopTask)
  const stopAll = useStore((s) => s.stopAll)

  const isRunning = currentId ? running.includes(currentId) : false

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

      <div
        className={`fp-status ${hotkeysAvailable ? 'is-ok' : 'is-bad'}`}
        title={hotkeysAvailable ? '全局快捷键已启用' : '全局快捷键不可用'}
      >
        <span className="fp-status-dot" />
        {hotkeysAvailable ? '快捷键已启用' : '仅手动运行'}
      </div>

      <div className="fp-toolbar-actions">
        {isRunning ? (
          <button
            type="button"
            className="fp-btn fp-btn-stop"
            onClick={() => currentId && stopTask(currentId)}
          >
            <Square size={15} /> 停止
          </button>
        ) : (
          <button
            type="button"
            className="fp-btn fp-btn-primary"
            disabled={!currentId}
            onClick={() => currentId && runTask(currentId)}
          >
            <Play size={15} /> 运行
          </button>
        )}
        <button type="button" className="fp-btn fp-btn-ghost" onClick={() => stopAll()}>
          <OctagonX size={15} /> 全部停止
        </button>
      </div>
    </header>
  )
}

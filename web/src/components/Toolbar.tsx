import { useRef } from 'react'
import { CheckCircle2, Code2, Download, FilePlus2, FolderOpen, Trash2, TriangleAlert } from 'lucide-react'

import { exportJson, exportPython, toWorkflow, validate } from '../codegen'
import { useStore } from '../store'
import type { Workflow } from '../types'

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function safeName(name: string): string {
  return name.trim().replace(/[^\w一-龥-]+/g, '_') || 'workflow'
}

export function Toolbar() {
  const fileInput = useRef<HTMLInputElement>(null)
  const nodes = useStore((s) => s.nodes)
  const edges = useStore((s) => s.edges)
  const workflowName = useStore((s) => s.workflowName)
  const dirty = useStore((s) => s.dirty)
  const setWorkflowName = useStore((s) => s.setWorkflowName)
  const removeSelected = useStore((s) => s.removeSelected)
  const resetWorkflow = useStore((s) => s.resetWorkflow)
  const loadWorkflow = useStore((s) => s.loadWorkflow)

  const wf = toWorkflow(nodes, edges, workflowName)
  const errors = validate(wf)
  const valid = errors.length === 0

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result)) as Workflow
        if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
          throw new Error('文件缺少 nodes/edges 字段')
        }
        loadWorkflow(parsed)
      } catch (err) {
        alert(`无法读取工作流：${err instanceof Error ? err.message : String(err)}`)
      }
    }
    reader.readAsText(file)
  }

  const handleExportPython = () => {
    if (!valid) {
      alert(`导出前请先修复：\n\n${errors.join('\n')}`)
      return
    }
    download(`${safeName(workflowName)}.py`, exportPython(wf), 'text/x-python')
  }

  return (
    <header className="fp-toolbar">
      <div className="fp-brand">
        <span className="fp-brand-mark">✦</span>
        <span className="fp-brand-name">FlowPilot Studio</span>
      </div>

      <input
        className="fp-name-input"
        value={workflowName}
        spellCheck={false}
        onChange={(e) => setWorkflowName(e.target.value)}
        aria-label="工作流名称"
      />
      {dirty && <span className="fp-dirty">●未保存</span>}

      <div className="fp-toolbar-spacer" />

      <div
        className={`fp-status ${valid ? 'is-ok' : 'is-bad'}`}
        title={valid ? '工作流有效' : errors.join('\n')}
      >
        {valid ? <CheckCircle2 size={15} /> : <TriangleAlert size={15} />}
        {valid ? '可导出' : `${errors.length} 个问题`}
      </div>

      <div className="fp-toolbar-actions">
        <button type="button" className="fp-btn" onClick={resetWorkflow}>
          <FilePlus2 size={15} /> 新建
        </button>
        <button type="button" className="fp-btn" onClick={() => fileInput.current?.click()}>
          <FolderOpen size={15} /> 打开
        </button>
        <button
          type="button"
          className="fp-btn"
          onClick={() => download(`${safeName(workflowName)}.flowpilot.json`, exportJson(wf), 'application/json')}
        >
          <Download size={15} /> 保存 JSON
        </button>
        <button type="button" className="fp-btn fp-btn-ghost" onClick={removeSelected}>
          <Trash2 size={15} /> 删除
        </button>
        <button type="button" className="fp-btn fp-btn-primary" onClick={handleExportPython}>
          <Code2 size={15} /> 导出脚本
        </button>
      </div>

      <input
        ref={fileInput}
        type="file"
        accept=".json,application/json"
        className="fp-hidden"
        onChange={handleImport}
      />
    </header>
  )
}

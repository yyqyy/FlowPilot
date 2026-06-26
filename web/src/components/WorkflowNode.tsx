import { Handle, Position, type NodeProps } from '@xyflow/react'

import type { FlowNode } from '../store'
import { NODE_META, type WorkflowNodeData } from '../types'

function configSummary(data: WorkflowNodeData): string {
  const c = data.config
  switch (data.kind) {
    case 'find_image': {
      const name = String(c.template ?? '').split(/[\\/]/).pop() || '未选择图片'
      return `${name} · ${Math.round(Number(c.threshold ?? 0.85) * 100)}%`
    }
    case 'click':
      return c.target === 'last_match' ? '点击上次匹配' : `(${c.x ?? 0}, ${c.y ?? 0})`
    case 'type_text': {
      const text = String(c.text ?? '')
      return text ? `"${text.slice(0, 18)}${text.length > 18 ? '…' : ''}"` : '空文本'
    }
    case 'delay':
      return `${c.min_seconds ?? 0}–${c.max_seconds ?? 0}s`
    default:
      return NODE_META[data.kind].hint
  }
}

export function WorkflowNode({ data, selected }: NodeProps<FlowNode>) {
  const meta = NODE_META[data.kind]
  return (
    <div
      className="fp-node"
      style={{
        boxShadow: selected
          ? `0 0 0 2px ${meta.accent}, 0 12px 30px -12px ${meta.accent}99`
          : undefined,
      }}
    >
      {meta.hasInput && (
        <Handle type="target" position={Position.Left} className="fp-handle" />
      )}
      <span className="fp-node-accent" style={{ background: meta.accent }} />
      <div className="fp-node-body">
        <div className="fp-node-title">{data.title}</div>
        <div className="fp-node-kind" style={{ color: meta.accent }}>
          {meta.label}
        </div>
        <div className="fp-node-summary">{configSummary(data)}</div>
      </div>
      {meta.hasOutput && (
        <Handle type="source" position={Position.Right} className="fp-handle" />
      )}
    </div>
  )
}

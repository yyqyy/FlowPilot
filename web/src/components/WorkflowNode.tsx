import { Handle, Position, type NodeProps } from '@xyflow/react'

import type { FlowNode } from '../store'
import { NODE_META, type WorkflowNodeData } from '../types'
import { ClickPreview } from './ClickPreview'

const WITH_IMAGE = new Set(['find_type', 'condition'])

function configSummary(data: WorkflowNodeData): string {
  const c = data.config
  switch (data.kind) {
    case 'find_click': {
      const name = String(c.template ?? '').split(/[\\/]/).pop()
      const where = name || (c.templateData ? '已嵌入图片' : '未选择图片')
      return c.button === 'double' ? `双击 ${where}` : c.button === 'right' ? `右键 ${where}` : where
    }
    case 'find_type':
      return String(c.text ?? '') ? `输入 "${String(c.text).slice(0, 14)}"` : '找到输入框'
    case 'type_text': {
      const text = String(c.text ?? '')
      return text ? `"${text.slice(0, 18)}${text.length > 18 ? '…' : ''}"` : '空文本'
    }
    case 'key_press':
      return String(c.keys ?? '') || '未设置按键'
    case 'delay':
      return `${c.min_seconds ?? 0}–${c.max_seconds ?? 0}s`
    case 'launch_app': {
      const path = String(c.path ?? '')
      return path ? (path.split(/[\\/]/).pop() ?? path) : '未选择程序'
    }
    case 'condition':
      return c.templateData || c.template ? '看到图片？' : '未选择图片'
    default:
      return NODE_META[data.kind].hint
  }
}

export function WorkflowNode({ data, selected }: NodeProps<FlowNode>) {
  const meta = NODE_META[data.kind]
  const templateData = String(data.config.templateData ?? '')
  const thumb = WITH_IMAGE.has(data.kind) ? templateData : ''
  const clickImage = data.kind === 'find_click' ? templateData : ''
  return (
    <div
      className="fp-node"
      style={{
        boxShadow: selected
          ? `0 0 0 2px ${meta.accent}, 0 12px 30px -12px ${meta.accent}99`
          : undefined,
      }}
    >
      {meta.hasInput && <Handle type="target" position={Position.Left} className="fp-handle" />}
      <span className="fp-node-accent" style={{ background: meta.accent }} />
      <div className="fp-node-body">
        <div className="fp-node-title">{data.title}</div>
        <div className="fp-node-kind" style={{ color: meta.accent }}>
          {meta.label}
        </div>
        <div className="fp-node-summary">{configSummary(data)}</div>
        {clickImage && (
          <ClickPreview
            src={clickImage}
            offsetX={Number(data.config.offsetX ?? 0)}
            offsetY={Number(data.config.offsetY ?? 0)}
            variant="node"
          />
        )}
        {thumb && <img className="fp-node-thumb" src={thumb} alt="" draggable={false} />}
      </div>

      {meta.branching ? (
        <>
          <Handle id="true" type="source" position={Position.Right} className="fp-handle fp-handle-true" style={{ top: '36%' }} />
          <Handle id="false" type="source" position={Position.Right} className="fp-handle fp-handle-false" style={{ top: '72%' }} />
          <span className="fp-port-label" style={{ top: 'calc(36% - 9px)' }}>是</span>
          <span className="fp-port-label" style={{ top: 'calc(72% - 9px)' }}>否</span>
        </>
      ) : meta.hasOutput ? (
        <Handle type="source" position={Position.Right} className="fp-handle" />
      ) : null}
    </div>
  )
}

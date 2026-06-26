// Domain model for FlowPilot workflows. Mirrors the executable semantics so the
// exported Python script behaves the same as the editor's preview.

export type NodeKind = 'start' | 'find_image' | 'click' | 'type_text' | 'delay' | 'stop'

export type ClickTarget = 'fixed' | 'last_match'

/** React Flow node `data`. Index signature keeps it assignable to the library's
 *  `Record<string, unknown>` data constraint. */
export interface WorkflowNodeData {
  kind: NodeKind
  title: string
  config: Record<string, unknown>
  [key: string]: unknown
}

/** Plain, serializable workflow (the saved/loaded .json shape). */
export interface WorkflowNode {
  id: string
  kind: NodeKind
  title: string
  x: number
  y: number
  config: Record<string, unknown>
}

export interface WorkflowEdge {
  source: string
  target: string
}

export interface Workflow {
  name: string
  version: number
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}

export interface NodeMeta {
  label: string
  accent: string
  hint: string
  hasInput: boolean
  hasOutput: boolean
}

export const NODE_META: Record<NodeKind, NodeMeta> = {
  start: { label: 'Start', accent: '#22c55e', hint: '工作流入口', hasInput: false, hasOutput: true },
  find_image: {
    label: 'Find image',
    accent: '#06b6d4',
    hint: '在屏幕上匹配模板图片',
    hasInput: true,
    hasOutput: true,
  },
  click: { label: 'Click', accent: '#8b5cf6', hint: '点击固定坐标或上次匹配', hasInput: true, hasOutput: true },
  type_text: { label: 'Type text', accent: '#f59e0b', hint: '输入一段文本', hasInput: true, hasOutput: true },
  delay: { label: 'Delay', accent: '#64748b', hint: '固定或随机延迟', hasInput: true, hasOutput: true },
  stop: { label: 'Stop', accent: '#ef4444', hint: '工作流结束', hasInput: true, hasOutput: false },
}

export function defaultConfig(kind: NodeKind): Record<string, unknown> {
  switch (kind) {
    case 'find_image':
      return { template: '', threshold: 0.85 }
    case 'click':
      return { target: 'fixed', x: 0, y: 0 }
    case 'type_text':
      return { text: '' }
    case 'delay':
      return { min_seconds: 0.5, max_seconds: 1.5 }
    default:
      return {}
  }
}

export function defaultTitle(kind: NodeKind): string {
  return NODE_META[kind].label
}

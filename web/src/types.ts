// Domain model for FlowPilot automation tasks. Mirrors the local engine so the
// editor and the runner agree on node semantics.

export type NodeKind =
  | 'start'
  | 'find_click'
  | 'find_type'
  | 'type_text'
  | 'key_press'
  | 'delay'
  | 'launch_app'
  | 'condition'
  | 'stop'

export type TriggerMode = 'once' | 'times' | 'loop'

/** React Flow node `data`. The index signature satisfies the library's
 *  `Record<string, unknown>` data constraint. */
export interface WorkflowNodeData {
  kind: NodeKind
  title: string
  config: Record<string, unknown>
  [key: string]: unknown
}

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
  label?: string
}

export interface Task {
  id: string
  name: string
  hotkey: string
  stop_hotkey: string
  trigger_mode: TriggerMode
  repeat: number
  enabled: boolean
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
}

export interface TaskSummary {
  id: string
  name: string
  hotkey: string
  stop_hotkey: string
  trigger_mode: TriggerMode
  repeat: number
  enabled: boolean
  nodeCount: number
}

export interface NodeMeta {
  label: string
  accent: string
  hint: string
  hasInput: boolean
  hasOutput: boolean
  branching?: boolean
}

export const NODE_META: Record<NodeKind, NodeMeta> = {
  start: { label: '开始', accent: '#22c55e', hint: '工作流入口', hasInput: false, hasOutput: true },
  find_click: {
    label: '找图点击',
    accent: '#06b6d4',
    hint: '在屏幕上找到图片并点击它',
    hasInput: true,
    hasOutput: true,
  },
  find_type: {
    label: '找图输入',
    accent: '#0ea5e9',
    hint: '找到输入框并输入文本',
    hasInput: true,
    hasOutput: true,
  },
  type_text: {
    label: '输入文本',
    accent: '#f59e0b',
    hint: '向当前焦点输入文本',
    hasInput: true,
    hasOutput: true,
  },
  key_press: {
    label: '按键',
    accent: '#eab308',
    hint: '按下按键或组合键',
    hasInput: true,
    hasOutput: true,
  },
  delay: { label: '延迟', accent: '#64748b', hint: '固定或随机等待', hasInput: true, hasOutput: true },
  launch_app: {
    label: '启动软件',
    accent: '#a855f7',
    hint: '打开一个程序',
    hasInput: true,
    hasOutput: true,
  },
  condition: {
    label: '判断',
    accent: '#ec4899',
    hint: '看到图片走"是"，否则走"否"',
    hasInput: true,
    hasOutput: true,
    branching: true,
  },
  stop: { label: '结束', accent: '#ef4444', hint: '工作流结束', hasInput: true, hasOutput: false },
}

export function defaultConfig(kind: NodeKind): Record<string, unknown> {
  switch (kind) {
    case 'find_click':
      return { templateData: '', template: '', threshold: 0.85, button: 'left', offsetX: 0, offsetY: 0 }
    case 'find_type':
      return { templateData: '', template: '', threshold: 0.85, text: '' }
    case 'type_text':
      return { text: '' }
    case 'key_press':
      return { keys: '' }
    case 'delay':
      return { min_seconds: 0.5, max_seconds: 1.5 }
    case 'launch_app':
      return { path: '', args: '', wait_seconds: 1 }
    case 'condition':
      return { templateData: '', template: '', threshold: 0.85 }
    default:
      return {}
  }
}

export function defaultTitle(kind: NodeKind): string {
  return NODE_META[kind].label
}

export const TRIGGER_LABELS: Record<TriggerMode, string> = {
  once: '执行一次',
  times: '执行多次',
  loop: '循环执行',
}

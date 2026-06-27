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
  | 'loop'
  | 'loop_while'
  | 'set_var'
  | 'check_var'
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

/** A labelled source port for branching/loop nodes (e.g. 是/否, 循环体/结束). */
export interface NodePort {
  id: string
  label: string
  top: string
  accent: string
}

export interface NodeMeta {
  label: string
  accent: string
  hint: string
  hasInput: boolean
  hasOutput: boolean
  branching?: boolean
  /** When set, the node renders these labelled source handles instead of one. */
  outputs?: NodePort[]
}

const YES_NO: NodePort[] = [
  { id: 'true', label: '是', top: '36%', accent: '#22c55e' },
  { id: 'false', label: '否', top: '72%', accent: '#ef4444' },
]

const BODY_DONE: NodePort[] = [
  { id: 'body', label: '循环体', top: '36%', accent: '#22c55e' },
  { id: 'done', label: '结束', top: '72%', accent: '#94a3b8' },
]

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
    outputs: YES_NO,
  },
  loop: {
    label: '重复循环',
    accent: '#8b5cf6',
    hint: '把"循环体"重复运行设定的次数',
    hasInput: true,
    hasOutput: true,
    branching: true,
    outputs: BODY_DONE,
  },
  loop_while: {
    label: '条件循环',
    accent: '#7c3aed',
    hint: '按图片或变量条件反复运行循环体',
    hasInput: true,
    hasOutput: true,
    branching: true,
    outputs: BODY_DONE,
  },
  set_var: {
    label: '设置变量',
    accent: '#14b8a6',
    hint: '把一个布尔变量设为真/假',
    hasInput: true,
    hasOutput: true,
  },
  check_var: {
    label: '判断变量',
    accent: '#0d9488',
    hint: '变量为真走"是"，否则走"否"',
    hasInput: true,
    hasOutput: true,
    branching: true,
    outputs: YES_NO,
  },
  stop: { label: '结束', accent: '#ef4444', hint: '工作流结束', hasInput: true, hasOutput: false },
}

// Screen-affecting actions wait 1s after running so the UI can react before the
// next find/click; control-flow nodes don't pause. Mirrors the engine default in
// runner._POST_DELAY_DEFAULT.
const POST_DELAY_KINDS = new Set<NodeKind>(['find_click', 'find_type', 'type_text', 'key_press'])

export function defaultPostDelay(kind: NodeKind): number {
  return POST_DELAY_KINDS.has(kind) ? 1 : 0
}

export function defaultConfig(kind: NodeKind): Record<string, unknown> {
  const post_delay = defaultPostDelay(kind)
  switch (kind) {
    case 'find_click':
      return { templateData: '', template: '', threshold: 0.85, button: 'left', offsetX: 0, offsetY: 0, post_delay }
    case 'find_type':
      return { templateData: '', template: '', threshold: 0.85, text: '', post_delay }
    case 'type_text':
      return { text: '', post_delay }
    case 'key_press':
      return { keys: '', post_delay }
    case 'delay':
      return { min_seconds: 0.5, max_seconds: 1.5, post_delay }
    case 'launch_app':
      return { path: '', args: '', wait_seconds: 1, post_delay }
    case 'condition':
      return { templateData: '', template: '', threshold: 0.85, result_var: '', post_delay }
    case 'loop':
      return { count: 3, post_delay }
    case 'loop_while':
      return { source: 'image', templateData: '', template: '', threshold: 0.85, varName: '', mode: 'true', max_iterations: 100, post_delay }
    case 'set_var':
      return { name: '', value: true, post_delay }
    case 'check_var':
      return { name: '', post_delay }
    default:
      return {}
  }
}

export function defaultTitle(kind: NodeKind): string {
  return NODE_META[kind].label
}

const PORT_LABELS: Record<string, string> = {
  true: '是',
  false: '否',
  body: '循环',
  done: '结束',
}

/** Chinese label shown on a branch/loop edge for a given source-handle id. */
export function portLabel(id: string | null | undefined): string | undefined {
  return id ? PORT_LABELS[id] : undefined
}

export const TRIGGER_LABELS: Record<TriggerMode, string> = {
  once: '执行一次',
  times: '执行多次',
  loop: '循环执行',
}

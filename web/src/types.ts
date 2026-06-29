// Domain model for FlowPilot automation tasks. Mirrors the local engine so the
// editor and the runner agree on node semantics. Pin layout mirrors
// src/flowpilot/engine/pins.py (NODE_PINS) — keep the two in sync.

export type NodeKind =
  | 'start'
  | 'find_click'
  | 'find_type'
  | 'type_text'
  | 'key_press'
  | 'delay'
  | 'launch_app'
  | 'condition'
  | 'branch'
  | 'loop'
  | 'loop_while'
  | 'swipe'
  | 'var_get'
  | 'var_set'
  | 'stop'

export type TriggerMode = 'once' | 'times' | 'loop'

export type VariableType = 'bool' | 'string' | 'point'

export interface Variable {
  id: string
  name: string
  type: VariableType
  default: unknown
}

export const VARIABLE_TYPE_LABELS: Record<VariableType, string> = {
  bool: '布尔',
  string: '文本',
  point: '坐标点',
}

export function defaultVarValue(type: VariableType): unknown {
  if (type === 'string') return ''
  if (type === 'point') return { x: 0, y: 0 }
  return false
}

// ---- Pins ----------------------------------------------------------------- //
export type PinKind = 'exec' | 'bool' | 'string' | 'point' | 'var'

export interface Pin {
  id: string
  dir: 'in' | 'out'
  kind: PinKind
  label: string
}

export const PIN_COLORS: Record<PinKind, string> = {
  exec: '#e2e8f0',
  bool: '#ef4444',
  string: '#ec4899',
  point: '#3b82f6',
  var: '#94a3b8',
}

export interface NodeSpec {
  label: string
  accent: string
  hint: string
  pins: Pin[]
}

const I = (kind: PinKind = 'exec', id = 'exec', label = ''): Pin => ({ id, dir: 'in', kind, label })
const O = (id: string, label: string, kind: PinKind = 'exec'): Pin => ({ id, dir: 'out', kind, label })

export const NODE_SPECS: Record<NodeKind, NodeSpec> = {
  start: { label: '开始', accent: '#22c55e', hint: '工作流入口', pins: [O('then', '')] },
  find_click: {
    label: '找图点击',
    accent: '#06b6d4',
    hint: '在屏幕上找到图片并点击它',
    pins: [I(), O('success', '成功'), O('fail', '失败'), O('found', '找到', 'bool')],
  },
  find_type: {
    label: '找图输入',
    accent: '#0ea5e9',
    hint: '找到输入框并输入文本',
    pins: [
      I(),
      I('string', 'text', '文本'),
      O('success', '成功'),
      O('fail', '失败'),
      O('found', '找到', 'bool'),
    ],
  },
  type_text: {
    label: '输入文本',
    accent: '#f59e0b',
    hint: '向当前焦点输入文本',
    pins: [I(), I('string', 'text', '文本'), O('then', '完成')],
  },
  key_press: {
    label: '按键',
    accent: '#eab308',
    hint: '按下按键或组合键',
    pins: [I(), O('then', '完成')],
  },
  delay: { label: '延迟', accent: '#64748b', hint: '固定或随机等待', pins: [I(), O('then', '完成')] },
  launch_app: {
    label: '启动软件',
    accent: '#a855f7',
    hint: '打开一个程序',
    pins: [I(), O('then', '完成')],
  },
  condition: {
    label: '看图判断',
    accent: '#ec4899',
    hint: '看到图片走"真"，否则走"假"',
    pins: [I(), O('true', '真'), O('false', '假'), O('found', '找到', 'bool')],
  },
  branch: {
    label: '分支',
    accent: '#f472b6',
    hint: '布尔为真走"真"，否则走"假"',
    pins: [I(), I('bool', 'cond', '条件'), O('true', '真'), O('false', '假')],
  },
  loop: {
    label: '重复循环',
    accent: '#8b5cf6',
    hint: '把"循环体"重复运行设定的次数',
    pins: [I(), O('body', '循环体'), O('done', '完成')],
  },
  loop_while: {
    label: '条件循环',
    accent: '#7c3aed',
    hint: '按布尔条件或图片反复运行循环体',
    pins: [I(), I('bool', 'cond', '条件'), O('body', '循环体'), O('done', '完成')],
  },
  swipe: {
    label: '滑动',
    accent: '#14b8a6',
    hint: '按序号在多个点之间按住拖动（点可按图查找或固定位置）',
    pins: [I(), O('success', '成功'), O('fail', '失败')],
  },
  var_get: {
    label: '获取变量',
    accent: '#94a3b8',
    hint: '输出一个变量的值（纯数据节点）',
    pins: [O('value', '值', 'var')],
  },
  var_set: {
    label: '设置变量',
    accent: '#0d9488',
    hint: '把一个值写入变量',
    pins: [I(), I('var', 'value', '值'), O('then', '完成')],
  },
  stop: { label: '结束', accent: '#ef4444', hint: '工作流结束', pins: [I()] },
}

export function inputPins(kind: NodeKind): Pin[] {
  return NODE_SPECS[kind].pins.filter((p) => p.dir === 'in')
}

export function outputPins(kind: NodeKind): Pin[] {
  return NODE_SPECS[kind].pins.filter((p) => p.dir === 'out')
}

export function findPin(kind: NodeKind, id: string | null | undefined): Pin | undefined {
  if (!id) return undefined
  return NODE_SPECS[kind].pins.find((p) => p.id === id)
}

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
  source_handle?: string
  target: string
  target_handle?: string
  kind?: 'exec' | 'data'
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
  variables: Variable[]
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

// Screen-affecting actions wait 1s after running so the UI can react before the
// next find/click; control-flow nodes don't pause. Mirrors the engine default in
// runner._POST_DELAY_DEFAULT.
const POST_DELAY_KINDS = new Set<NodeKind>([
  'find_click',
  'find_type',
  'type_text',
  'key_press',
  'swipe',
])

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
      return { templateData: '', template: '', threshold: 0.85, post_delay }
    case 'branch':
      return { post_delay }
    case 'loop':
      return { count: 3, post_delay }
    case 'loop_while':
      return { source: 'image', templateData: '', template: '', threshold: 0.85, mode: 'true', max_iterations: 100, post_delay }
    case 'swipe':
      return { screenshotData: '', shotW: 0, shotH: 0, points: [], durations: [], button: 'left', post_delay }
    case 'var_get':
      return { name: '' }
    case 'var_set':
      return { name: '', value: false, post_delay }
    default:
      return {}
  }
}

export function defaultTitle(kind: NodeKind): string {
  return NODE_SPECS[kind].label
}

/** A var-pin's real type is the type of the variable its node points at; other
 *  pins use their declared kind. Returns null for an unknown pin. */
export function effectivePinType(
  kind: NodeKind,
  pinId: string | null | undefined,
  varName: string | undefined,
  variables: Variable[],
): PinKind | null {
  const pin = findPin(kind, pinId)
  if (!pin) return null
  if (pin.kind === 'var') {
    const v = variables.find((x) => x.name === varName)
    return v ? v.type : 'var'
  }
  return pin.kind
}

/** exec only joins exec; data joins same-typed data ('var' acts as wildcard). */
export function pinsCompatible(a: PinKind | null, b: PinKind | null): boolean {
  if (!a || !b) return false
  if (a === 'exec' || b === 'exec') return a === 'exec' && b === 'exec'
  return a === b || a === 'var' || b === 'var'
}

export const TRIGGER_LABELS: Record<TriggerMode, string> = {
  once: '执行一次',
  times: '执行多次',
  loop: '循环执行',
}

import { create } from 'zustand'
import {
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
} from '@xyflow/react'

import { api } from './api'
import {
  defaultConfig,
  defaultTitle,
  defaultVarValue,
  effectivePinType,
  PIN_COLORS,
  pinsCompatible,
  type NodeKind,
  type PinKind,
  type Task,
  type TaskSummary,
  type TriggerMode,
  type Variable,
  type VariableType,
  type WorkflowNodeData,
} from './types'

export type FlowNode = Node<WorkflowNodeData>
export type FlowEdge = Edge<{ kind: 'exec' | 'data' }>

const EXEC_COLOR = '#94a3b8'

let counter = 0
function newId(prefix: string): string {
  counter += 1
  return `${prefix}-${Date.now().toString(36)}-${counter}-${Math.random().toString(36).slice(2, 7)}`
}

function makeNode(kind: NodeKind, position: { x: number; y: number }): FlowNode {
  return {
    id: newId(kind),
    type: 'flow',
    position,
    deletable: kind !== 'start' && kind !== 'stop',
    data: { kind, title: defaultTitle(kind), config: defaultConfig(kind) },
  }
}

function makeVarNode(name: string, mode: 'get' | 'set', position: { x: number; y: number }): FlowNode {
  const kind: NodeKind = mode === 'get' ? 'var_get' : 'var_set'
  return {
    id: newId(kind),
    type: 'flow',
    position,
    deletable: true,
    data: {
      kind,
      title: `${mode === 'get' ? '获取' : '设置'} ${name}`,
      config: { ...defaultConfig(kind), name },
    },
  }
}

function edgeId(source: string, sh: string | null, target: string, th: string | null): string {
  return `e-${source}.${sh ?? ''}-${target}.${th ?? ''}`
}

function makeEdge(
  source: string,
  sourceHandle: string | null,
  target: string,
  targetHandle: string | null,
  kind: 'exec' | 'data',
  color: string,
): FlowEdge {
  return {
    id: edgeId(source, sourceHandle, target, targetHandle),
    source,
    target,
    sourceHandle: sourceHandle ?? null,
    targetHandle: targetHandle ?? null,
    type: 'smoothstep',
    animated: kind === 'exec',
    data: { kind },
    style: { stroke: color, strokeWidth: 2, strokeDasharray: kind === 'data' ? '6 4' : undefined },
  }
}

function configName(node: FlowNode | undefined): string | undefined {
  return node ? String(node.data.config.name ?? '') : undefined
}

/** Validate a drag-created connection. Returns the wire kind + colour, or null
 *  when the pins are incompatible (exec↔exec, data↔matching-data only). */
function validateConnection(
  connection: Connection | Edge,
  nodes: FlowNode[],
  variables: Variable[],
): { kind: 'exec' | 'data'; color: string } | null {
  const { source, target, sourceHandle, targetHandle } = connection
  if (!source || !target || source === target) return null
  const sNode = nodes.find((n) => n.id === source)
  const tNode = nodes.find((n) => n.id === target)
  if (!sNode || !tNode) return null
  const sType = effectivePinType(sNode.data.kind, sourceHandle, configName(sNode), variables)
  const tType = effectivePinType(tNode.data.kind, targetHandle, configName(tNode), variables)
  if (!pinsCompatible(sType, tType)) return null
  const kind: 'exec' | 'data' = sType === 'exec' ? 'exec' : 'data'
  const concrete: PinKind = sType && sType !== 'var' ? sType : tType && tType !== 'var' ? tType : 'var'
  return { kind, color: kind === 'exec' ? EXEC_COLOR : PIN_COLORS[concrete] }
}

interface Settings {
  name: string
  hotkey: string
  stop_hotkey: string
  trigger_mode: TriggerMode
  repeat: number
  enabled: boolean
}

interface StoreState {
  tasks: TaskSummary[]
  currentId: string | null
  nodes: FlowNode[]
  edges: FlowEdge[]
  variables: Variable[]
  settings: Settings
  running: string[]
  hotkeysAvailable: boolean
  log: string[]
  ready: boolean

  init: () => Promise<void>
  refreshTasks: () => Promise<void>
  refreshStatus: () => Promise<void>
  selectTask: (id: string) => Promise<void>
  createTask: () => Promise<void>
  deleteTask: (id: string) => Promise<void>
  runTask: (id: string) => Promise<void>
  stopTask: (id: string) => Promise<void>
  stopAll: () => Promise<void>

  onNodesChange: (changes: NodeChange<FlowNode>[]) => void
  onEdgesChange: (changes: EdgeChange<FlowEdge>[]) => void
  onConnect: (connection: Connection) => void
  isValidConnection: (connection: Connection | Edge) => boolean
  addNode: (kind: NodeKind, position: { x: number; y: number }) => void
  addImageNode: (name: string, dataUrl: string, position: { x: number; y: number }) => void
  addVarNode: (name: string, mode: 'get' | 'set', position: { x: number; y: number }) => void
  setNodeImage: (id: string, name: string, dataUrl: string) => void
  clearNodeImage: (id: string) => void
  updateConfig: (id: string, key: string, value: unknown) => void
  updateConfigMany: (id: string, patch: Record<string, unknown>) => void
  renameNode: (id: string, title: string) => void
  removeSelected: () => void
  copySelection: () => void
  paste: () => void
  duplicateSelected: () => void
  updateSettings: (patch: Partial<Settings>) => void

  addVariable: () => void
  renameVariable: (id: string, name: string) => void
  retypeVariable: (id: string, type: VariableType) => void
  removeVariable: (id: string) => void

  buildTask: () => Task | null
  scheduleSave: () => void
}

const DEFAULT_SETTINGS: Settings = {
  name: '新任务',
  hotkey: '',
  stop_hotkey: '',
  trigger_mode: 'once',
  repeat: 1,
  enabled: true,
}

let saveTimer: ReturnType<typeof setTimeout> | null = null

// Copy/paste buffer for box-selected nodes (UE5-blueprint style duplication).
let clipboard: { nodes: FlowNode[]; edges: FlowEdge[] } | null = null

export const useStore = create<StoreState>((set, get) => ({
  tasks: [],
  currentId: null,
  nodes: [],
  edges: [],
  variables: [],
  settings: { ...DEFAULT_SETTINGS },
  running: [],
  hotkeysAvailable: false,
  log: [],
  ready: false,

  init: async () => {
    await get().refreshTasks()
    const { tasks } = get()
    if (tasks.length === 0) {
      await get().createTask()
    } else {
      await get().selectTask(tasks[0].id)
    }
    await get().refreshStatus()
    set({ ready: true })
  },

  refreshTasks: async () => {
    try {
      set({ tasks: await api.listTasks() })
    } catch {
      /* engine offline */
    }
  },

  refreshStatus: async () => {
    try {
      const s = await api.status()
      set({ running: s.running, hotkeysAvailable: s.hotkeys, log: s.log })
    } catch {
      /* engine offline */
    }
  },

  selectTask: async (id) => {
    const task = await api.getTask(id)
    const variables = task.variables ?? []
    const nodes: FlowNode[] = task.nodes.map((n) => ({
      id: n.id,
      type: 'flow',
      position: { x: n.x, y: n.y },
      deletable: n.kind !== 'start' && n.kind !== 'stop',
      data: { kind: n.kind, title: n.title, config: { ...n.config } },
    }))
    const kindById = new Map(task.nodes.map((n) => [n.id, n] as const))
    const edges: FlowEdge[] = task.edges.map((e) => {
      const kind = e.kind === 'data' ? 'data' : 'exec'
      const src = kindById.get(e.source)
      const sType = src
        ? effectivePinType(src.kind, e.source_handle, String(src.config.name ?? ''), variables)
        : null
      const concrete: PinKind = sType && sType !== 'var' ? sType : 'var'
      const color = kind === 'exec' ? EXEC_COLOR : PIN_COLORS[concrete]
      return makeEdge(
        e.source,
        e.source_handle ?? null,
        e.target,
        e.target_handle ?? null,
        kind,
        color,
      )
    })
    set({
      currentId: id,
      nodes,
      edges,
      variables,
      settings: {
        name: task.name,
        hotkey: task.hotkey,
        stop_hotkey: task.stop_hotkey,
        trigger_mode: task.trigger_mode,
        repeat: task.repeat,
        enabled: task.enabled,
      },
    })
  },

  createTask: async () => {
    const task = await api.createTask('新任务')
    await get().refreshTasks()
    await get().selectTask(task.id)
  },

  deleteTask: async (id) => {
    await api.deleteTask(id)
    await get().refreshTasks()
    const { tasks, currentId } = get()
    if (currentId === id) {
      if (tasks.length > 0) await get().selectTask(tasks[0].id)
      else await get().createTask()
    }
  },

  runTask: async (id) => {
    try {
      await api.runTask(id)
    } finally {
      await get().refreshStatus()
    }
  },

  stopTask: async (id) => {
    await api.stopTask(id)
    await get().refreshStatus()
  },

  stopAll: async () => {
    await api.stopAll()
    await get().refreshStatus()
  },

  onNodesChange: (changes) => {
    set((s) => ({ nodes: applyNodeChanges(changes, s.nodes) }))
    if (changes.some((c) => c.type === 'position' || c.type === 'remove' || c.type === 'add')) {
      get().scheduleSave()
    }
  },

  onEdgesChange: (changes) => {
    set((s) => ({ edges: applyEdgeChanges(changes, s.edges) }))
    if (changes.some((c) => c.type === 'remove' || c.type === 'add')) get().scheduleSave()
  },

  isValidConnection: (connection) => {
    const { nodes, variables } = get()
    return validateConnection(connection, nodes, variables) !== null
  },

  onConnect: (connection) => {
    const { source, target, sourceHandle, targetHandle } = connection
    const { nodes, variables } = get()
    const verdict = validateConnection(connection, nodes, variables)
    if (!verdict || !source || !target) return
    set((s) => {
      const pruned = s.edges.filter((e) => {
        const intoSameTarget = e.target === target && (e.targetHandle ?? null) === (targetHandle ?? null)
        const outSameExec =
          verdict.kind === 'exec' &&
          e.source === source &&
          (e.sourceHandle ?? null) === (sourceHandle ?? null)
        return !intoSameTarget && !outSameExec
      })
      const edge = makeEdge(source, sourceHandle ?? null, target, targetHandle ?? null, verdict.kind, verdict.color)
      return { edges: addEdge(edge, pruned) }
    })
    get().scheduleSave()
  },

  addNode: (kind, position) => {
    set((s) => ({ nodes: [...s.nodes, makeNode(kind, position)] }))
    get().scheduleSave()
  },

  addImageNode: (name, dataUrl, position) => {
    const node: FlowNode = {
      id: newId('find_click'),
      type: 'flow',
      position,
      deletable: true,
      data: {
        kind: 'find_click',
        title: name ? `点击：${name}` : '找图点击',
        config: { ...defaultConfig('find_click'), template: name, templateData: dataUrl },
      },
    }
    set((s) => ({ nodes: [...s.nodes, node] }))
    get().scheduleSave()
  },

  addVarNode: (name, mode, position) => {
    set((s) => ({ nodes: [...s.nodes, makeVarNode(name, mode, position)] }))
    get().scheduleSave()
  },

  setNodeImage: (id, name, dataUrl) => {
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, config: { ...n.data.config, template: name, templateData: dataUrl } } }
          : n,
      ),
    }))
    get().scheduleSave()
  },

  clearNodeImage: (id) => {
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, config: { ...n.data.config, template: '', templateData: '' } } }
          : n,
      ),
    }))
    get().scheduleSave()
  },

  updateConfig: (id, key, value) => {
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, config: { ...n.data.config, [key]: value } } } : n,
      ),
    }))
    get().scheduleSave()
  },

  updateConfigMany: (id, patch) => {
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, config: { ...n.data.config, ...patch } } } : n,
      ),
    }))
    get().scheduleSave()
  },

  renameNode: (id, title) => {
    set((s) => ({
      nodes: s.nodes.map((n) => (n.id === id ? { ...n, data: { ...n.data, title } } : n)),
    }))
    get().scheduleSave()
  },

  removeSelected: () => {
    set((s) => {
      const toRemove = new Set(
        s.nodes
          .filter((n) => n.selected && n.data.kind !== 'start' && n.data.kind !== 'stop')
          .map((n) => n.id),
      )
      const selectedEdges = new Set(s.edges.filter((e) => e.selected).map((e) => e.id))
      if (toRemove.size === 0 && selectedEdges.size === 0) return {}
      return {
        nodes: s.nodes.filter((n) => !toRemove.has(n.id)),
        edges: s.edges.filter(
          (e) => !selectedEdges.has(e.id) && !toRemove.has(e.source) && !toRemove.has(e.target),
        ),
      }
    })
    get().scheduleSave()
  },

  copySelection: () => {
    const { nodes, edges } = get()
    const selected = nodes.filter(
      (n) => n.selected && n.data.kind !== 'start' && n.data.kind !== 'stop',
    )
    if (selected.length === 0) return
    const ids = new Set(selected.map((n) => n.id))
    clipboard = {
      nodes: selected.map((n) => ({ ...n, data: { ...n.data, config: { ...n.data.config } } })),
      edges: edges.filter((e) => ids.has(e.source) && ids.has(e.target)),
    }
  },

  paste: () => {
    if (!clipboard || clipboard.nodes.length === 0) return
    const idMap = new Map<string, string>()
    const OFFSET = 48
    const newNodes: FlowNode[] = clipboard.nodes.map((n) => {
      const id = newId(n.data.kind)
      idMap.set(n.id, id)
      return {
        ...n,
        id,
        position: { x: n.position.x + OFFSET, y: n.position.y + OFFSET },
        selected: true,
        data: { ...n.data, config: { ...n.data.config } },
      }
    })
    const newEdges: FlowEdge[] = clipboard.edges.map((e) => {
      const source = idMap.get(e.source) as string
      const target = idMap.get(e.target) as string
      return {
        ...e,
        id: edgeId(source, e.sourceHandle ?? null, target, e.targetHandle ?? null),
        source,
        target,
        selected: false,
      }
    })
    set((s) => ({
      nodes: [...s.nodes.map((n) => ({ ...n, selected: false })), ...newNodes],
      edges: [...s.edges, ...newEdges],
    }))
    get().scheduleSave()
  },

  duplicateSelected: () => {
    get().copySelection()
    get().paste()
  },

  updateSettings: (patch) => {
    set((s) => ({ settings: { ...s.settings, ...patch } }))
    get().scheduleSave()
  },

  addVariable: () => {
    set((s) => {
      const used = new Set(s.variables.map((v) => v.name))
      let i = s.variables.length + 1
      let name = `变量${i}`
      while (used.has(name)) name = `变量${++i}`
      const variable: Variable = { id: newId('var'), name, type: 'bool', default: false }
      return { variables: [...s.variables, variable] }
    })
    get().scheduleSave()
  },

  renameVariable: (id, name) => {
    set((s) => {
      const old = s.variables.find((v) => v.id === id)
      if (!old) return {}
      const nodes = s.nodes.map((n) =>
        (n.data.kind === 'var_get' || n.data.kind === 'var_set') && n.data.config.name === old.name
          ? {
              ...n,
              data: {
                ...n.data,
                title: `${n.data.kind === 'var_get' ? '获取' : '设置'} ${name}`,
                config: { ...n.data.config, name },
              },
            }
          : n,
      )
      return {
        variables: s.variables.map((v) => (v.id === id ? { ...v, name } : v)),
        nodes,
      }
    })
    get().scheduleSave()
  },

  retypeVariable: (id, type) => {
    set((s) => {
      const target = s.variables.find((v) => v.id === id)
      if (!target) return {}
      const fresh = defaultVarValue(type)
      const nodes = s.nodes.map((n) =>
        n.data.kind === 'var_set' && n.data.config.name === target.name
          ? { ...n, data: { ...n.data, config: { ...n.data.config, value: fresh } } }
          : n,
      )
      return {
        variables: s.variables.map((v) => (v.id === id ? { ...v, type, default: fresh } : v)),
        nodes,
      }
    })
    get().scheduleSave()
  },

  removeVariable: (id) => {
    set((s) => ({ variables: s.variables.filter((v) => v.id !== id) }))
    get().scheduleSave()
  },

  buildTask: () => {
    const { currentId, nodes, edges, variables, settings } = get()
    if (!currentId) return null
    return {
      id: currentId,
      name: settings.name,
      hotkey: settings.hotkey,
      stop_hotkey: settings.stop_hotkey,
      trigger_mode: settings.trigger_mode,
      repeat: settings.repeat,
      enabled: settings.enabled,
      variables,
      nodes: nodes.map((n) => ({
        id: n.id,
        kind: n.data.kind,
        title: n.data.title,
        x: Math.round(n.position.x),
        y: Math.round(n.position.y),
        config: { ...n.data.config },
      })),
      edges: edges.map((e) => ({
        source: e.source,
        source_handle: (e.sourceHandle as string | null) ?? 'then',
        target: e.target,
        target_handle: (e.targetHandle as string | null) ?? 'exec',
        kind: e.data?.kind ?? 'exec',
      })),
    }
  },

  scheduleSave: () => {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => {
      const task = get().buildTask()
      if (!task) return
      api
        .saveTask(task)
        .then(() => get().refreshTasks())
        .catch(() => {})
    }, 500)
  },
}))

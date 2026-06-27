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
  portLabel,
  type NodeKind,
  type Task,
  type TaskSummary,
  type TriggerMode,
  type WorkflowNodeData,
} from './types'

export type FlowNode = Node<WorkflowNodeData>
export type FlowEdge = Edge

const EDGE_STYLE = { type: 'smoothstep', animated: true } as const

let counter = 0
function newId(kind: NodeKind): string {
  counter += 1
  return `${kind}-${Date.now().toString(36)}-${counter}-${Math.random().toString(36).slice(2, 7)}`
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

function edgeLabel(edge: FlowEdge): string {
  return (edge.sourceHandle as string | null | undefined) || 'next'
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
  onEdgesChange: (changes: EdgeChange[]) => void
  onConnect: (connection: Connection) => void
  addNode: (kind: NodeKind, position: { x: number; y: number }) => void
  addImageNode: (name: string, dataUrl: string, position: { x: number; y: number }) => void
  setNodeImage: (id: string, name: string, dataUrl: string) => void
  clearNodeImage: (id: string) => void
  updateConfig: (id: string, key: string, value: unknown) => void
  renameNode: (id: string, title: string) => void
  removeSelected: () => void
  copySelection: () => void
  paste: () => void
  duplicateSelected: () => void
  updateSettings: (patch: Partial<Settings>) => void

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
    const nodes: FlowNode[] = task.nodes.map((n) => ({
      id: n.id,
      type: 'flow',
      position: { x: n.x, y: n.y },
      deletable: n.kind !== 'start' && n.kind !== 'stop',
      data: { kind: n.kind, title: n.title, config: { ...n.config } },
    }))
    const edges: FlowEdge[] = task.edges.map((e) => ({
      id: `e-${e.source}-${e.target}-${e.label ?? 'next'}`,
      source: e.source,
      target: e.target,
      sourceHandle: e.label && e.label !== 'next' ? e.label : null,
      label: portLabel(e.label),
      ...EDGE_STYLE,
    }))
    set({
      currentId: id,
      nodes,
      edges,
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

  onConnect: (connection) => {
    const { source, target, sourceHandle } = connection
    if (!source || !target || source === target) return
    const label = sourceHandle || 'next'
    set((s) => {
      // one outgoing edge per (source, handle)
      const pruned = s.edges.filter((e) => !(e.source === source && edgeLabel(e) === label))
      const edge: FlowEdge = {
        id: `e-${source}-${target}-${label}`,
        source,
        target,
        sourceHandle: sourceHandle ?? null,
        label: portLabel(label),
        ...EDGE_STYLE,
      }
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
      return { ...e, id: `e-${source}-${target}-${edgeLabel(e)}`, source, target, selected: false }
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

  buildTask: () => {
    const { currentId, nodes, edges, settings } = get()
    if (!currentId) return null
    return {
      id: currentId,
      name: settings.name,
      hotkey: settings.hotkey,
      stop_hotkey: settings.stop_hotkey,
      trigger_mode: settings.trigger_mode,
      repeat: settings.repeat,
      enabled: settings.enabled,
      nodes: nodes.map((n) => ({
        id: n.id,
        kind: n.data.kind,
        title: n.data.title,
        x: Math.round(n.position.x),
        y: Math.round(n.position.y),
        config: { ...n.data.config },
      })),
      edges: edges.map((e) => ({ source: e.source, target: e.target, label: edgeLabel(e) })),
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

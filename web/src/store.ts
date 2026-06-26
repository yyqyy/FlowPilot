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

import {
  defaultConfig,
  defaultTitle,
  type NodeKind,
  type Workflow,
  type WorkflowNodeData,
} from './types'

export type FlowNode = Node<WorkflowNodeData>
export type FlowEdge = Edge

const EDGE_STYLE = {
  type: 'smoothstep',
  animated: true,
  style: { stroke: '#64748b', strokeWidth: 2 },
} as const

let counter = 0
function newId(kind: NodeKind): string {
  counter += 1
  const rand = Math.random().toString(36).slice(2, 8)
  return `${kind}-${Date.now().toString(36)}-${counter}-${rand}`
}

function makeNode(kind: NodeKind, position: { x: number; y: number }): FlowNode {
  return {
    id: newId(kind),
    type: 'flow',
    position,
    data: { kind, title: defaultTitle(kind), config: defaultConfig(kind) },
  }
}

interface StoreState {
  nodes: FlowNode[]
  edges: FlowEdge[]
  workflowName: string
  dirty: boolean

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
  setWorkflowName: (name: string) => void

  selectedNode: () => FlowNode | null
  loadWorkflow: (wf: Workflow) => void
  resetWorkflow: () => void
}

function starterNodes(): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const start: FlowNode = {
    id: newId('start'),
    type: 'flow',
    position: { x: 80, y: 200 },
    deletable: false,
    data: { kind: 'start', title: 'Start', config: {} },
  }
  const delay = makeNode('delay', { x: 380, y: 200 })
  const stop: FlowNode = {
    id: newId('stop'),
    type: 'flow',
    position: { x: 680, y: 200 },
    deletable: false,
    data: { kind: 'stop', title: 'Stop', config: {} },
  }
  return {
    nodes: [start, delay, stop],
    edges: [
      { id: `e-${start.id}-${delay.id}`, source: start.id, target: delay.id, ...EDGE_STYLE },
      { id: `e-${delay.id}-${stop.id}`, source: delay.id, target: stop.id, ...EDGE_STYLE },
    ],
  }
}

const initial = starterNodes()

function isStructuralChange(changes: NodeChange<FlowNode>[]): boolean {
  return changes.some((c) => c.type === 'position' || c.type === 'add' || c.type === 'remove')
}

export const useStore = create<StoreState>((set, get) => ({
  nodes: initial.nodes,
  edges: initial.edges,
  workflowName: 'First workflow',
  dirty: false,

  onNodesChange: (changes) =>
    set((s) => ({
      nodes: applyNodeChanges(changes, s.nodes),
      dirty: s.dirty || isStructuralChange(changes),
    })),

  onEdgesChange: (changes) =>
    set((s) => ({
      edges: applyEdgeChanges(changes, s.edges),
      dirty: s.dirty || changes.some((c) => c.type === 'remove' || c.type === 'add'),
    })),

  onConnect: (connection) => {
    const { source, target } = connection
    if (!source || !target || source === target) return
    set((s) => {
      // One outgoing connection per node: drop any existing edge from this source.
      const pruned = s.edges.filter((e) => e.source !== source)
      const edge: FlowEdge = {
        id: `e-${source}-${target}`,
        source,
        target,
        ...EDGE_STYLE,
      }
      return { edges: addEdge(edge, pruned), dirty: true }
    })
  },

  addNode: (kind, position) =>
    set((s) => ({ nodes: [...s.nodes, makeNode(kind, position)], dirty: true })),

  addImageNode: (name, dataUrl, position) =>
    set((s) => {
      const node: FlowNode = {
        id: newId('find_image'),
        type: 'flow',
        position,
        data: {
          kind: 'find_image',
          title: name ? `找图：${name}` : 'Find image',
          config: { template: name, templateData: dataUrl, threshold: 0.85 },
        },
      }
      return { nodes: [...s.nodes, node], dirty: true }
    }),

  setNodeImage: (id, name, dataUrl) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id
          ? {
              ...n,
              data: {
                ...n.data,
                config: { ...n.data.config, template: name, templateData: dataUrl },
              },
            }
          : n,
      ),
      dirty: true,
    })),

  clearNodeImage: (id) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, config: { ...n.data.config, template: '', templateData: '' } } }
          : n,
      ),
      dirty: true,
    })),

  updateConfig: (id, key, value) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, config: { ...n.data.config, [key]: value } } } : n,
      ),
      dirty: true,
    })),

  renameNode: (id, title) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === id ? { ...n, data: { ...n.data, title } } : n,
      ),
      dirty: true,
    })),

  removeSelected: () =>
    set((s) => {
      // Start and Stop are required for a valid workflow, so they are never deletable.
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
        dirty: true,
      }
    }),

  setWorkflowName: (name) => set({ workflowName: name, dirty: true }),

  selectedNode: () => get().nodes.find((n) => n.selected) ?? null,

  loadWorkflow: (wf) =>
    set(() => {
      const nodes: FlowNode[] = wf.nodes.map((n) => ({
        id: n.id,
        type: 'flow',
        position: { x: n.x, y: n.y },
        deletable: n.kind !== 'start' && n.kind !== 'stop',
        data: { kind: n.kind, title: n.title, config: { ...n.config } },
      }))
      const edges: FlowEdge[] = wf.edges.map((e) => ({
        id: `e-${e.source}-${e.target}`,
        source: e.source,
        target: e.target,
        ...EDGE_STYLE,
      }))
      return { nodes, edges, workflowName: wf.name || 'Untitled workflow', dirty: false }
    }),

  resetWorkflow: () =>
    set(() => {
      const fresh = starterNodes()
      return { ...fresh, workflowName: 'Untitled workflow', dirty: false }
    }),
}))

import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  type NodeTypes,
} from '@xyflow/react'

import { useStore } from '../store'
import { NODE_META, type NodeKind, type WorkflowNodeData } from '../types'
import { WorkflowNode } from './WorkflowNode'

const nodeTypes: NodeTypes = { flow: WorkflowNode }

function miniMapColor(kind: NodeKind | undefined): string {
  return kind ? NODE_META[kind].accent : '#64748b'
}

export function FlowCanvas() {
  const nodes = useStore((s) => s.nodes)
  const edges = useStore((s) => s.edges)
  const onNodesChange = useStore((s) => s.onNodesChange)
  const onEdgesChange = useStore((s) => s.onEdgesChange)
  const onConnect = useStore((s) => s.onConnect)

  return (
    <div className="fp-canvas">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        minZoom={0.25}
        maxZoom={2.5}
        deleteKeyCode={['Delete', 'Backspace']}
        defaultEdgeOptions={{ type: 'smoothstep' }}
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1.5} color="#1e293b" />
        <MiniMap
          pannable
          zoomable
          maskColor="rgba(2,6,23,0.6)"
          nodeColor={(n) => miniMapColor((n.data as WorkflowNodeData | undefined)?.kind)}
        />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  )
}

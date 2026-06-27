import { useCallback, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useReactFlow,
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
  const addImageNode = useStore((s) => s.addImageNode)
  const addNode = useStore((s) => s.addNode)
  const { screenToFlowPosition } = useReactFlow()
  const [dropping, setDropping] = useState(false)

  const onDragOver = useCallback((event: React.DragEvent) => {
    const types = event.dataTransfer.types
    if (types.includes('Files') || types.includes('application/flowpilot-node')) {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'copy'
      setDropping(true)
    }
  }, [])

  const onDragLeave = useCallback((event: React.DragEvent) => {
    if (event.currentTarget === event.target) setDropping(false)
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      setDropping(false)
      const origin = screenToFlowPosition({ x: event.clientX, y: event.clientY })

      const kind = event.dataTransfer.getData('application/flowpilot-node')
      if (kind) {
        addNode(kind as NodeKind, origin)
        return
      }

      const images = Array.from(event.dataTransfer.files).filter((f) => f.type.startsWith('image/'))
      images.forEach((file, index) => {
        const reader = new FileReader()
        reader.onload = () =>
          addImageNode(file.name, String(reader.result), {
            x: origin.x + index * 32,
            y: origin.y + index * 32,
          })
        reader.readAsDataURL(file)
      })
    },
    [screenToFlowPosition, addImageNode, addNode],
  )

  return (
    <div
      className={`fp-canvas${dropping ? ' is-dropping' : ''}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {dropping && <div className="fp-drop-hint">松手即可创建图片节点</div>}
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

import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  SelectionMode,
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

function canAcceptDrag(event: React.DragEvent): boolean {
  const types = event.dataTransfer.types
  return types.includes('Files') || types.includes('application/flowpilot-node')
}

export function FlowCanvas() {
  const nodes = useStore((s) => s.nodes)
  const edges = useStore((s) => s.edges)
  const onNodesChange = useStore((s) => s.onNodesChange)
  const onEdgesChange = useStore((s) => s.onEdgesChange)
  const onConnect = useStore((s) => s.onConnect)
  const addImageNode = useStore((s) => s.addImageNode)
  const addNode = useStore((s) => s.addNode)
  const copySelection = useStore((s) => s.copySelection)
  const paste = useStore((s) => s.paste)
  const duplicateSelected = useStore((s) => s.duplicateSelected)
  const { screenToFlowPosition } = useReactFlow()
  const [dropping, setDropping] = useState(false)
  // Count enter/leave so passing over child elements doesn't clear the hint;
  // window-level dragend/drop force-reset it when a drag is cancelled outside.
  const dragDepth = useRef(0)

  useEffect(() => {
    const reset = () => {
      dragDepth.current = 0
      setDropping(false)
    }
    window.addEventListener('dragend', reset)
    window.addEventListener('drop', reset)
    return () => {
      window.removeEventListener('dragend', reset)
      window.removeEventListener('drop', reset)
    }
  }, [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null
      const tag = target?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable) return
      if (!(event.ctrlKey || event.metaKey)) return
      const key = event.key.toLowerCase()
      if (key === 'c') {
        copySelection()
      } else if (key === 'v') {
        event.preventDefault()
        paste()
      } else if (key === 'd') {
        event.preventDefault()
        duplicateSelected()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [copySelection, paste, duplicateSelected])

  const onDragEnter = useCallback((event: React.DragEvent) => {
    if (!canAcceptDrag(event)) return
    event.preventDefault()
    dragDepth.current += 1
    setDropping(true)
  }, [])

  const onDragOver = useCallback((event: React.DragEvent) => {
    if (!canAcceptDrag(event)) return
    event.preventDefault()
    event.dataTransfer.dropEffect = 'copy'
  }, [])

  const onDragLeave = useCallback((event: React.DragEvent) => {
    if (!canAcceptDrag(event)) return
    dragDepth.current = Math.max(0, dragDepth.current - 1)
    if (dragDepth.current === 0) setDropping(false)
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      dragDepth.current = 0
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
      onDragEnter={onDragEnter}
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
        selectionOnDrag
        selectionMode={SelectionMode.Partial}
        selectionKeyCode={null}
        multiSelectionKeyCode={['Meta', 'Shift', 'Control']}
        panOnDrag={[1, 2]}
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

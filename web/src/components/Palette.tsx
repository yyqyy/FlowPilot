import { Clock, Crosshair, Image, Keyboard, Plus } from 'lucide-react'

import { useStore } from '../store'
import { NODE_META, type NodeKind } from '../types'

const ICONS: Record<string, typeof Plus> = {
  find_image: Image,
  click: Crosshair,
  type_text: Keyboard,
  delay: Clock,
}

const ADDABLE: NodeKind[] = ['find_image', 'click', 'type_text', 'delay']

export function Palette() {
  const addNode = useStore((s) => s.addNode)
  const nodeCount = useStore((s) => s.nodes.length)

  return (
    <nav className="fp-palette">
      <div className="fp-palette-title">添加节点</div>
      {ADDABLE.map((kind, index) => {
        const meta = NODE_META[kind]
        const Icon = ICONS[kind] ?? Plus
        return (
          <button
            key={kind}
            type="button"
            className="fp-palette-item"
            onClick={() =>
              addNode(kind, { x: 360 + (nodeCount % 4) * 36 + index * 6, y: 360 + (nodeCount % 5) * 28 })
            }
          >
            <span className="fp-palette-icon" style={{ background: `${meta.accent}22`, color: meta.accent }}>
              <Icon size={16} />
            </span>
            <span className="fp-palette-label">
              <span>{meta.label}</span>
              <span className="fp-palette-hint">{meta.hint}</span>
            </span>
          </button>
        )
      })}
      <div className="fp-palette-tip">
        从节点右侧圆点拖到另一个节点左侧圆点即可连线。选中后按 Delete 删除。
      </div>
    </nav>
  )
}

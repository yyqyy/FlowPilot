import {
  Clock,
  Diamond,
  GitBranch,
  Keyboard,
  MousePointerClick,
  Plus,
  Repeat,
  Repeat2,
  Rocket,
  TextCursorInput,
  Type,
  Variable,
} from 'lucide-react'

import { useStore } from '../store'
import { NODE_META, type NodeKind } from '../types'

const ICONS: Record<string, typeof Plus> = {
  find_click: MousePointerClick,
  find_type: TextCursorInput,
  type_text: Type,
  key_press: Keyboard,
  delay: Clock,
  launch_app: Rocket,
  condition: GitBranch,
  loop: Repeat,
  loop_while: Repeat2,
  set_var: Variable,
  check_var: Diamond,
}

const ADDABLE: NodeKind[] = [
  'find_click',
  'find_type',
  'type_text',
  'key_press',
  'delay',
  'launch_app',
  'condition',
  'loop',
  'loop_while',
  'set_var',
  'check_var',
]

export function Palette() {
  const addNode = useStore((s) => s.addNode)
  const count = useStore((s) => s.nodes.length)

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
            draggable
            onDragStart={(e) => {
              e.dataTransfer.setData('application/flowpilot-node', kind)
              e.dataTransfer.effectAllowed = 'copy'
            }}
            onClick={() =>
              addNode(kind, { x: 360 + (count % 4) * 30 + index * 4, y: 320 + (count % 6) * 26 })
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
        从节点右侧圆点拖到另一个节点连线。判断有"是/否"、循环有"循环体/结束"两个出口（把循环体末尾连回循环节点即可重复）。
        左键空白处框选多个节点，Ctrl+C/V 复制、Ctrl+D 原地复制。把图片拖到画布可直接生成找图点击节点。
      </div>
    </nav>
  )
}

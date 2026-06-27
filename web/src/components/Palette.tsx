import {
  Clock,
  GitBranch,
  Keyboard,
  MousePointerClick,
  Move,
  Plus,
  Repeat,
  Repeat2,
  Rocket,
  Split,
  TextCursorInput,
  Type,
} from 'lucide-react'

import { useStore } from '../store'
import { NODE_SPECS, type NodeKind } from '../types'

const ICONS: Record<string, typeof Plus> = {
  find_click: MousePointerClick,
  find_type: TextCursorInput,
  type_text: Type,
  key_press: Keyboard,
  delay: Clock,
  launch_app: Rocket,
  swipe: Move,
  condition: GitBranch,
  branch: Split,
  loop: Repeat,
  loop_while: Repeat2,
}

const ADDABLE: NodeKind[] = [
  'find_click',
  'find_type',
  'type_text',
  'key_press',
  'delay',
  'launch_app',
  'swipe',
  'condition',
  'branch',
  'loop',
  'loop_while',
]

export function Palette() {
  const addNode = useStore((s) => s.addNode)
  const count = useStore((s) => s.nodes.length)

  return (
    <nav className="fp-palette">
      <div className="fp-palette-title">添加节点</div>
      {ADDABLE.map((kind, index) => {
        const meta = NODE_SPECS[kind]
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
        白色方口是执行线（控制顺序），彩色圆口是数据线（传值）。从节点右侧的口拖到另一个节点左侧的口连线。
        找图点击/判断有「成功·失败」或「真·假」出口。变量在下方面板新建后，把「获取/设置」拖到画布即可。
        左键空白处框选，Ctrl+C/V 复制、Ctrl+D 原地复制；把图片拖到画布生成找图点击节点。
      </div>
    </nav>
  )
}

import { Plus, Trash2 } from 'lucide-react'

import { useStore } from '../store'
import { PIN_COLORS, VARIABLE_TYPE_LABELS, type VariableType } from '../types'

const TYPES: VariableType[] = ['bool', 'string', 'point']

function VarChip({ name, mode }: { name: string; mode: 'get' | 'set' }) {
  const addVarNode = useStore((s) => s.addVarNode)
  return (
    <button
      type="button"
      className="fp-var-chip"
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData('application/flowpilot-var', JSON.stringify({ name, mode }))
        e.dataTransfer.effectAllowed = 'copy'
      }}
      onClick={() => addVarNode(name, mode, { x: 420, y: 320 })}
    >
      {mode === 'get' ? '获取' : '设置'}
    </button>
  )
}

export function VariablesPanel() {
  const variables = useStore((s) => s.variables)
  const addVariable = useStore((s) => s.addVariable)
  const renameVariable = useStore((s) => s.renameVariable)
  const retypeVariable = useStore((s) => s.retypeVariable)
  const removeVariable = useStore((s) => s.removeVariable)

  return (
    <div className="fp-vars">
      <div className="fp-vars-head">
        <span>变量</span>
        <button type="button" className="fp-icon-btn" title="新建变量" onClick={addVariable}>
          <Plus size={15} />
        </button>
      </div>

      {variables.length === 0 ? (
        <div className="fp-var-empty">
          还没有变量。点上面的「+」新建，然后把「获取 / 设置」拖到画布上，用数据线连接节点。
        </div>
      ) : (
        variables.map((v) => (
          <div className="fp-var-row" key={v.id}>
            <div className="fp-var-top">
              <span className="fp-var-dot" style={{ background: PIN_COLORS[v.type] }} />
              <input
                className="fp-var-name"
                value={v.name}
                onChange={(e) => renameVariable(v.id, e.target.value)}
              />
              <select
                className="fp-var-type"
                value={v.type}
                onChange={(e) => retypeVariable(v.id, e.target.value as VariableType)}
              >
                {TYPES.map((t) => (
                  <option key={t} value={t}>
                    {VARIABLE_TYPE_LABELS[t]}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="fp-var-del"
                title="删除变量"
                onClick={() => removeVariable(v.id)}
              >
                <Trash2 size={14} />
              </button>
            </div>
            <div className="fp-var-actions">
              <VarChip name={v.name} mode="get" />
              <VarChip name={v.name} mode="set" />
            </div>
          </div>
        ))
      )}
    </div>
  )
}

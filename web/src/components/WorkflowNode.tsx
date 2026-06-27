import { Fragment } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'

import { useStore, type FlowNode } from '../store'
import {
  inputPins,
  NODE_SPECS,
  outputPins,
  PIN_COLORS,
  type Pin,
  type VariableType,
  type WorkflowNodeData,
} from '../types'
import { ClickPreview } from './ClickPreview'

const WITH_TEMPLATE = new Set(['find_type', 'condition', 'loop_while'])

function configSummary(data: WorkflowNodeData): string {
  const c = data.config
  switch (data.kind) {
    case 'find_click': {
      const name = String(c.template ?? '').split(/[\\/]/).pop()
      const where = name || (c.templateData ? '已嵌入图片' : '未选择图片')
      return c.button === 'double' ? `双击 ${where}` : c.button === 'right' ? `右键 ${where}` : where
    }
    case 'find_type':
      return String(c.text ?? '') ? `输入 "${String(c.text).slice(0, 14)}"` : '找到输入框'
    case 'type_text': {
      const text = String(c.text ?? '')
      return text ? `"${text.slice(0, 18)}${text.length > 18 ? '…' : ''}"` : '空文本'
    }
    case 'key_press':
      return String(c.keys ?? '') || '未设置按键'
    case 'delay':
      return `${c.min_seconds ?? 0}–${c.max_seconds ?? 0}s`
    case 'launch_app': {
      const path = String(c.path ?? '')
      return path ? (path.split(/[\\/]/).pop() ?? path) : '未选择程序'
    }
    case 'condition':
      return c.templateData || c.template ? '看到图片？' : '未选择图片'
    case 'branch':
      return '布尔为真？'
    case 'loop':
      return `重复 ${Number(c.count ?? 0)} 次`
    case 'loop_while':
      return '条件成立时循环'
    case 'swipe': {
      const n = Array.isArray(c.points) ? c.points.length : 0
      return n >= 2 ? `${n} 个点滑动` : '未设置滑动点'
    }
    case 'var_get':
      return String(c.name ?? '') ? `获取 ${String(c.name)}` : '未选择变量'
    case 'var_set':
      return String(c.name ?? '') ? `设置 ${String(c.name)}` : '未选择变量'
    default:
      return NODE_SPECS[data.kind].hint
  }
}

function topFor(index: number, count: number): string {
  return `${((index + 1) / (count + 1)) * 100}%`
}

export function WorkflowNode({ data, selected }: NodeProps<FlowNode>) {
  const meta = NODE_SPECS[data.kind]
  const variables = useStore((s) => s.variables)
  const varType: VariableType | undefined =
    data.kind === 'var_get' || data.kind === 'var_set'
      ? variables.find((v) => v.name === data.config.name)?.type
      : undefined

  const colorOf = (pin: Pin): string =>
    pin.kind === 'var' ? (varType ? PIN_COLORS[varType] : PIN_COLORS.var) : PIN_COLORS[pin.kind]

  const inputs = inputPins(data.kind)
  const outputs = outputPins(data.kind)

  const templateData = String(data.config.templateData ?? '')
  const thumb = WITH_TEMPLATE.has(data.kind)
    ? templateData
    : data.kind === 'swipe'
      ? String(data.config.screenshotData ?? '')
      : ''
  const clickImage = data.kind === 'find_click' ? templateData : ''

  const renderPin = (pin: Pin, index: number, count: number, side: 'in' | 'out') => {
    const top = topFor(index, count)
    const color = colorOf(pin)
    const isExec = pin.kind === 'exec'
    return (
      <Fragment key={`${side}-${pin.id}`}>
        <Handle
          id={pin.id}
          type={side === 'in' ? 'target' : 'source'}
          position={side === 'in' ? Position.Left : Position.Right}
          className={`fp-pin ${isExec ? 'fp-pin-exec' : 'fp-pin-data'}`}
          style={isExec ? { top } : { top, background: color, borderColor: color }}
        />
        {pin.label && (
          <span
            className={`fp-pin-label ${side === 'in' ? 'fp-pin-label-in' : 'fp-pin-label-out'}`}
            style={{ top: `calc(${top} - 8px)` }}
          >
            {pin.label}
          </span>
        )}
      </Fragment>
    )
  }

  return (
    <div
      className={`fp-node${data.kind === 'var_get' ? ' fp-node-pure' : ''}`}
      style={{
        boxShadow: selected
          ? `0 0 0 2px ${meta.accent}, 0 12px 30px -12px ${meta.accent}99`
          : undefined,
      }}
    >
      {inputs.map((pin, i) => renderPin(pin, i, inputs.length, 'in'))}
      <span className="fp-node-accent" style={{ background: meta.accent }} />
      <div className="fp-node-body">
        <div className="fp-node-title">{data.title}</div>
        <div className="fp-node-kind" style={{ color: meta.accent }}>
          {meta.label}
        </div>
        <div className="fp-node-summary">{configSummary(data)}</div>
        {clickImage && (
          <ClickPreview
            src={clickImage}
            offsetX={Number(data.config.offsetX ?? 0)}
            offsetY={Number(data.config.offsetY ?? 0)}
            variant="node"
          />
        )}
        {thumb && <img className="fp-node-thumb" src={thumb} alt="" draggable={false} />}
      </div>
      {outputs.map((pin, i) => renderPin(pin, i, outputs.length, 'out'))}
    </div>
  )
}

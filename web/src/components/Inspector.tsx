import { useRef, useState } from 'react'
import { ImagePlus } from 'lucide-react'

import { useStore, type FlowNode } from '../store'
import { NODE_META, TRIGGER_LABELS, type NodeKind, type TriggerMode } from '../types'
import { ClickPreview } from './ClickPreview'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="fp-field">
      <span className="fp-field-label">{label}</span>
      {children}
    </label>
  )
}

function HotkeyInput({
  value,
  onChange,
  placeholder,
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
}) {
  const [recording, setRecording] = useState(false)

  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!recording) return
    event.preventDefault()
    const key = event.key.toLowerCase()
    if (['control', 'alt', 'shift', 'meta'].includes(key)) return
    const parts: string[] = []
    if (event.ctrlKey) parts.push('ctrl')
    if (event.altKey) parts.push('alt')
    if (event.shiftKey) parts.push('shift')
    parts.push(key === ' ' ? 'space' : key)
    onChange(parts.join('+'))
    setRecording(false)
    event.currentTarget.blur()
  }

  return (
    <div className="fp-hotkey">
      <input
        className="fp-input"
        readOnly
        value={recording ? '按下组合键…' : value}
        placeholder={placeholder ?? '点击后按下快捷键'}
        onKeyDown={onKeyDown}
        onFocus={() => setRecording(true)}
        onBlur={() => setRecording(false)}
      />
      {value && (
        <button type="button" className="fp-link fp-link-danger" onClick={() => onChange('')}>
          清除
        </button>
      )}
    </div>
  )
}

function ImagePicker({ node }: { node: FlowNode }) {
  const fileRef = useRef<HTMLInputElement>(null)
  const setNodeImage = useStore((s) => s.setNodeImage)
  const clearNodeImage = useStore((s) => s.clearNodeImage)
  const updateConfig = useStore((s) => s.updateConfig)
  const config = node.data.config
  const dataUrl = String(config.templateData ?? '')
  const name = String(config.template ?? '')
  const threshold = Number(config.threshold ?? 0.85)

  const onPick = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setNodeImage(node.id, file.name, String(reader.result))
    reader.readAsDataURL(file)
  }

  return (
    <>
      <Field label="目标图片">
        {dataUrl ? (
          <div className="fp-image-preview">
            <img src={dataUrl} alt={name} />
            <div className="fp-image-meta">
              <span className="fp-image-name" title={name}>
                {name || '已嵌入图片'}
              </span>
              <div className="fp-image-actions">
                <button type="button" className="fp-link" onClick={() => fileRef.current?.click()}>
                  更换
                </button>
                <button
                  type="button"
                  className="fp-link fp-link-danger"
                  onClick={() => clearNodeImage(node.id)}
                >
                  移除
                </button>
              </div>
            </div>
          </div>
        ) : (
          <button type="button" className="fp-image-drop" onClick={() => fileRef.current?.click()}>
            <ImagePlus size={18} />
            <span>点击选择图片，或把图片拖到画布上</span>
          </button>
        )}
        <input ref={fileRef} type="file" accept="image/*" className="fp-hidden" onChange={onPick} />
      </Field>
      <Field label={`匹配精度 ${Math.round(threshold * 100)}%`}>
        <input
          className="fp-range"
          type="range"
          min={0.5}
          max={1}
          step={0.01}
          value={threshold}
          onChange={(e) => updateConfig(node.id, 'threshold', Number(e.target.value))}
        />
      </Field>
    </>
  )
}

function TaskSettings() {
  const settings = useStore((s) => s.settings)
  const update = useStore((s) => s.updateSettings)
  const hotkeysAvailable = useStore((s) => s.hotkeysAvailable)

  return (
    <aside className="fp-inspector">
      <div className="fp-inspector-head">
        <span className="fp-dot" style={{ background: '#38bdf8' }} />
        <span>任务设置</span>
      </div>

      <Field label="任务名称">
        <input
          className="fp-input"
          value={settings.name}
          onChange={(e) => update({ name: e.target.value })}
        />
      </Field>

      <Field label="触发方式">
        <div className="fp-segment">
          {(['once', 'times', 'loop'] as TriggerMode[]).map((mode) => (
            <button
              key={mode}
              type="button"
              className={`fp-segment-item${settings.trigger_mode === mode ? ' is-active' : ''}`}
              onClick={() => update({ trigger_mode: mode })}
            >
              {TRIGGER_LABELS[mode]}
            </button>
          ))}
        </div>
      </Field>

      {settings.trigger_mode === 'times' && (
        <Field label="执行次数">
          <input
            className="fp-input"
            type="number"
            min={1}
            value={settings.repeat}
            onChange={(e) => update({ repeat: Math.max(1, Number(e.target.value)) })}
          />
        </Field>
      )}

      <Field label="启动快捷键">
        <HotkeyInput value={settings.hotkey} onChange={(v) => update({ hotkey: v })} />
      </Field>
      <Field label="停止快捷键">
        <HotkeyInput value={settings.stop_hotkey} onChange={(v) => update({ stop_hotkey: v })} />
      </Field>

      <label className="fp-check">
        <input
          type="checkbox"
          checked={settings.enabled}
          onChange={(e) => update({ enabled: e.target.checked })}
        />
        <span>启用快捷键监听</span>
      </label>

      <div className="fp-inspector-empty">
        {hotkeysAvailable
          ? '再次按下启动快捷键会从头重启当前任务。'
          : '全局快捷键当前不可用，可在左侧用▶按钮手动运行。'}
      </div>
    </aside>
  )
}

const PICKER_KINDS = new Set<NodeKind>(['find_click', 'find_type', 'condition'])

export function Inspector() {
  const nodes = useStore((s) => s.nodes)
  const updateConfig = useStore((s) => s.updateConfig)
  const renameNode = useStore((s) => s.renameNode)

  const node = nodes.find((n) => n.selected) ?? null
  if (!node) return <TaskSettings />

  const { kind, title, config } = node.data
  const meta = NODE_META[kind]
  const setCfg = (key: string, value: unknown) => updateConfig(node.id, key, value)

  return (
    <aside className="fp-inspector">
      <div className="fp-inspector-head">
        <span className="fp-dot" style={{ background: meta.accent }} />
        <span>{meta.label}</span>
      </div>

      <Field label="名称">
        <input className="fp-input" value={title} onChange={(e) => renameNode(node.id, e.target.value)} />
      </Field>

      {PICKER_KINDS.has(kind) && <ImagePicker node={node} />}

      {kind === 'find_click' && (
        <>
          <Field label="点击方式">
            <select className="fp-input" value={String(config.button ?? 'left')} onChange={(e) => setCfg('button', e.target.value)}>
              <option value="left">左键单击</option>
              <option value="right">右键单击</option>
              <option value="double">双击</option>
            </select>
          </Field>
          <div className="fp-row">
            <Field label="X 偏移">
              <input className="fp-input" type="number" value={Number(config.offsetX ?? 0)} onChange={(e) => setCfg('offsetX', Number(e.target.value))} />
            </Field>
            <Field label="Y 偏移">
              <input className="fp-input" type="number" value={Number(config.offsetY ?? 0)} onChange={(e) => setCfg('offsetY', Number(e.target.value))} />
            </Field>
          </div>
          {String(config.templateData ?? '') && (
            <Field label="点击位置（红点）">
              <ClickPreview
                src={String(config.templateData)}
                offsetX={Number(config.offsetX ?? 0)}
                offsetY={Number(config.offsetY ?? 0)}
                variant="inspector"
              />
            </Field>
          )}
        </>
      )}

      {kind === 'find_type' && (
        <Field label="输入文本">
          <textarea className="fp-input fp-textarea" rows={4} value={String(config.text ?? '')} onChange={(e) => setCfg('text', e.target.value)} />
        </Field>
      )}

      {kind === 'type_text' && (
        <Field label="文本内容">
          <textarea className="fp-input fp-textarea" rows={5} value={String(config.text ?? '')} onChange={(e) => setCfg('text', e.target.value)} />
        </Field>
      )}

      {kind === 'key_press' && (
        <Field label="按键 / 组合键">
          <HotkeyInput value={String(config.keys ?? '')} onChange={(v) => setCfg('keys', v)} placeholder="点击后按下按键" />
        </Field>
      )}

      {kind === 'delay' && (
        <div className="fp-row">
          <Field label="最小秒数">
            <input className="fp-input" type="number" min={0} step={0.1} value={Number(config.min_seconds ?? 0.5)} onChange={(e) => setCfg('min_seconds', Number(e.target.value))} />
          </Field>
          <Field label="最大秒数">
            <input className="fp-input" type="number" min={0} step={0.1} value={Number(config.max_seconds ?? 1.5)} onChange={(e) => setCfg('max_seconds', Number(e.target.value))} />
          </Field>
        </div>
      )}

      {kind === 'launch_app' && (
        <>
          <Field label="程序路径">
            <input className="fp-input" placeholder="例如 C:\Windows\notepad.exe" value={String(config.path ?? '')} onChange={(e) => setCfg('path', e.target.value)} />
          </Field>
          <Field label="启动参数（可选）">
            <input className="fp-input" value={String(config.args ?? '')} onChange={(e) => setCfg('args', e.target.value)} />
          </Field>
          <Field label="启动后等待（秒）">
            <input className="fp-input" type="number" min={0} step={0.5} value={Number(config.wait_seconds ?? 1)} onChange={(e) => setCfg('wait_seconds', Number(e.target.value))} />
          </Field>
        </>
      )}

      {(kind === 'start' || kind === 'stop') && (
        <div className="fp-inspector-empty">{meta.hint}（必需节点，不可删除）。</div>
      )}
    </aside>
  )
}

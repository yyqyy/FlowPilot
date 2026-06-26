import { useStore } from '../store'
import { NODE_META, type ClickTarget } from '../types'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="fp-field">
      <span className="fp-field-label">{label}</span>
      {children}
    </label>
  )
}

export function Inspector() {
  const nodes = useStore((s) => s.nodes)
  const updateConfig = useStore((s) => s.updateConfig)
  const renameNode = useStore((s) => s.renameNode)

  const node = nodes.find((n) => n.selected) ?? null

  if (!node) {
    return (
      <aside className="fp-inspector">
        <div className="fp-inspector-empty">选中一个节点来编辑它的属性。</div>
      </aside>
    )
  }

  const { kind, title, config } = node.data
  const meta = NODE_META[kind]

  return (
    <aside className="fp-inspector">
      <div className="fp-inspector-head">
        <span className="fp-dot" style={{ background: meta.accent }} />
        <span>{meta.label}</span>
      </div>

      <Field label="名称">
        <input
          className="fp-input"
          value={title}
          onChange={(e) => renameNode(node.id, e.target.value)}
        />
      </Field>

      {kind === 'find_image' && (
        <>
          <Field label="模板图片路径">
            <input
              className="fp-input"
              placeholder="例如 assets/templates/button.png"
              value={String(config.template ?? '')}
              onChange={(e) => updateConfig(node.id, 'template', e.target.value)}
            />
          </Field>
          <Field label={`置信度 ${Math.round(Number(config.threshold ?? 0.85) * 100)}%`}>
            <input
              className="fp-range"
              type="range"
              min={0.5}
              max={1}
              step={0.01}
              value={Number(config.threshold ?? 0.85)}
              onChange={(e) => updateConfig(node.id, 'threshold', Number(e.target.value))}
            />
          </Field>
        </>
      )}

      {kind === 'click' && (
        <>
          <Field label="点击目标">
            <select
              className="fp-input"
              value={String(config.target ?? 'fixed')}
              onChange={(e) => updateConfig(node.id, 'target', e.target.value as ClickTarget)}
            >
              <option value="fixed">固定坐标</option>
              <option value="last_match">上次图片匹配</option>
            </select>
          </Field>
          {config.target !== 'last_match' && (
            <div className="fp-row">
              <Field label="X">
                <input
                  className="fp-input"
                  type="number"
                  value={Number(config.x ?? 0)}
                  onChange={(e) => updateConfig(node.id, 'x', Number(e.target.value))}
                />
              </Field>
              <Field label="Y">
                <input
                  className="fp-input"
                  type="number"
                  value={Number(config.y ?? 0)}
                  onChange={(e) => updateConfig(node.id, 'y', Number(e.target.value))}
                />
              </Field>
            </div>
          )}
        </>
      )}

      {kind === 'type_text' && (
        <Field label="文本内容">
          <textarea
            className="fp-input fp-textarea"
            rows={5}
            value={String(config.text ?? '')}
            onChange={(e) => updateConfig(node.id, 'text', e.target.value)}
          />
        </Field>
      )}

      {kind === 'delay' && (
        <div className="fp-row">
          <Field label="最小秒数">
            <input
              className="fp-input"
              type="number"
              min={0}
              step={0.1}
              value={Number(config.min_seconds ?? 0.5)}
              onChange={(e) => updateConfig(node.id, 'min_seconds', Number(e.target.value))}
            />
          </Field>
          <Field label="最大秒数">
            <input
              className="fp-input"
              type="number"
              min={0}
              step={0.1}
              value={Number(config.max_seconds ?? 1.5)}
              onChange={(e) => updateConfig(node.id, 'max_seconds', Number(e.target.value))}
            />
          </Field>
        </div>
      )}

      {(kind === 'start' || kind === 'stop') && (
        <div className="fp-inspector-empty">{meta.hint}（必需节点，不可删除）。</div>
      )}
    </aside>
  )
}

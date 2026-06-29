import { useEffect, useRef, useState } from 'react'
import { ImagePlus, Maximize2, Trash2, X } from 'lucide-react'

import { useStore, type FlowNode } from '../store'

type PointMode = 'image' | 'screen'

interface SwipePoint {
  mode: PointMode
  x: number // centre, in screenshot pixels
  y: number
  w: number // template box size (image mode)
  h: number
  template?: string // cropped image to find at run time (image mode)
  threshold: number
  offsetX: number
  offsetY: number
}

interface Box {
  cx: number
  cy: number
  w: number
  h: number
}

const clamp = (v: number, max: number) => Math.max(0, Math.min(max, v))
const CLICK_SLOP = 5 // px in screenshot space: smaller drag => a fixed-position click

function adjustDurations(durations: number[], segments: number): number[] {
  const out = durations.slice(0, Math.max(0, segments))
  while (out.length < segments) out.push(0.3)
  return out
}

function normalizePoint(raw: unknown): SwipePoint {
  const p = (raw ?? {}) as Record<string, unknown>
  return {
    mode: p.mode === 'image' ? 'image' : 'screen',
    x: Number(p.x ?? 0),
    y: Number(p.y ?? 0),
    w: Number(p.w ?? 0),
    h: Number(p.h ?? 0),
    template: typeof p.template === 'string' ? p.template : undefined,
    threshold: Number(p.threshold ?? 0.85),
    offsetX: Number(p.offsetX ?? 0),
    offsetY: Number(p.offsetY ?? 0),
  }
}

/** The screenshot canvas: drag a box to add a find-image point, click to add a
 *  fixed point, drag a badge to move it, double-click a badge to delete. */
function SwipeStage({
  src,
  shotW,
  shotH,
  points,
  onAddImage,
  onAddScreen,
  onMove,
  onMoveEnd,
  onRemove,
}: {
  src: string
  shotW: number
  shotH: number
  points: SwipePoint[]
  onAddImage: (box: Box) => void
  onAddScreen: (x: number, y: number) => void
  onMove: (index: number, x: number, y: number) => void
  onMoveEnd: (index: number) => void
  onRemove: (index: number) => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [drag, setDrag] = useState<number | null>(null)
  const [sel, setSel] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null)
  const safeW = shotW || 1
  const safeH = shotH || 1

  const toImage = (clientX: number, clientY: number) => {
    const r = ref.current!.getBoundingClientRect()
    return {
      x: clamp(Math.round(((clientX - r.left) / r.width) * shotW), shotW),
      y: clamp(Math.round(((clientY - r.top) / r.height) * shotH), shotH),
    }
  }

  // Dragging an existing point.
  useEffect(() => {
    if (drag === null) return
    const move = (e: MouseEvent) => {
      const p = toImage(e.clientX, e.clientY)
      onMove(drag, p.x, p.y)
    }
    const up = () => {
      onMoveEnd(drag)
      setDrag(null)
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
    return () => {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', up)
    }
  }, [drag]) // eslint-disable-line react-hooks/exhaustive-deps

  // Drawing a selection box (or a click) on empty canvas.
  useEffect(() => {
    if (sel === null) return
    const move = (e: MouseEvent) => {
      const p = toImage(e.clientX, e.clientY)
      setSel((s) => (s ? { ...s, x1: p.x, y1: p.y } : s))
    }
    const up = () => {
      setSel((s) => {
        if (s) {
          const w = Math.abs(s.x1 - s.x0)
          const h = Math.abs(s.y1 - s.y0)
          if (w < CLICK_SLOP && h < CLICK_SLOP) {
            onAddScreen(s.x0, s.y0)
          } else {
            onAddImage({ cx: (s.x0 + s.x1) / 2, cy: (s.y0 + s.y1) / 2, w, h })
          }
        }
        return null
      })
    }
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
    return () => {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', up)
    }
  }, [sel]) // eslint-disable-line react-hooks/exhaustive-deps

  const onStageMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).classList.contains('fp-swipe-point')) return
    const p = toImage(e.clientX, e.clientY)
    setSel({ x0: p.x, y0: p.y, x1: p.x, y1: p.y })
  }

  return (
    <div className="fp-swipe-stage" ref={ref} onMouseDown={onStageMouseDown}>
      <img src={src} alt="" draggable={false} />

      {points.length >= 2 && (
        <svg className="fp-swipe-line" viewBox={`0 0 ${safeW} ${safeH}`} preserveAspectRatio="none">
          <polyline
            points={points.map((p) => `${p.x},${p.y}`).join(' ')}
            fill="none"
            stroke="#38bdf8"
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      )}

      {sel && (
        <div
          className="fp-swipe-sel"
          style={{
            left: `${(Math.min(sel.x0, sel.x1) / safeW) * 100}%`,
            top: `${(Math.min(sel.y0, sel.y1) / safeH) * 100}%`,
            width: `${(Math.abs(sel.x1 - sel.x0) / safeW) * 100}%`,
            height: `${(Math.abs(sel.y1 - sel.y0) / safeH) * 100}%`,
          }}
        />
      )}

      {points.map((p, i) => (
        <div key={i} className="fp-swipe-marker">
          {p.mode === 'image' && p.w > 0 && (
            <div
              className="fp-swipe-box"
              style={{
                left: `${((p.x - p.w / 2) / safeW) * 100}%`,
                top: `${((p.y - p.h / 2) / safeH) * 100}%`,
                width: `${(p.w / safeW) * 100}%`,
                height: `${(p.h / safeH) * 100}%`,
              }}
            />
          )}
          <div
            className={`fp-swipe-point${p.mode === 'screen' ? ' is-screen' : ''}`}
            style={{ left: `${(p.x / safeW) * 100}%`, top: `${(p.y / safeH) * 100}%` }}
            title="拖动移动，双击删除"
            onMouseDown={(e) => {
              e.stopPropagation()
              setDrag(i)
            }}
            onDoubleClick={(e) => {
              e.stopPropagation()
              onRemove(i)
            }}
          >
            {i + 1}
          </div>
        </div>
      ))}
    </div>
  )
}

export function SwipeEditor({ node }: { node: FlowNode }) {
  const fileRef = useRef<HTMLInputElement>(null)
  const cropImgRef = useRef<HTMLImageElement>(null)
  const updateConfig = useStore((s) => s.updateConfig)
  const updateConfigMany = useStore((s) => s.updateConfigMany)
  const [zoom, setZoom] = useState(false)

  const config = node.data.config
  const src = String(config.screenshotData ?? '')
  const shotW = Number(config.shotW ?? 0)
  const shotH = Number(config.shotH ?? 0)
  const points = (Array.isArray(config.points) ? config.points : []).map(normalizePoint)
  const durations = (Array.isArray(config.durations) ? config.durations : []) as number[]

  const cropTemplate = (cx: number, cy: number, w: number, h: number): string => {
    const img = cropImgRef.current
    if (!img || !img.complete || w < 1 || h < 1) return ''
    const cw = Math.round(w)
    const ch = Math.round(h)
    const canvas = document.createElement('canvas')
    canvas.width = cw
    canvas.height = ch
    const g = canvas.getContext('2d')
    if (!g) return ''
    g.drawImage(img, Math.round(cx - w / 2), Math.round(cy - h / 2), w, h, 0, 0, cw, ch)
    try {
      return canvas.toDataURL('image/png')
    } catch {
      return ''
    }
  }

  const writePoints = (next: SwipePoint[]) =>
    updateConfigMany(node.id, { points: next, durations: adjustDurations(durations, next.length - 1) })

  const addImage = (box: Box) =>
    writePoints([
      ...points,
      {
        mode: 'image',
        x: Math.round(box.cx),
        y: Math.round(box.cy),
        w: Math.round(box.w),
        h: Math.round(box.h),
        template: cropTemplate(box.cx, box.cy, box.w, box.h),
        threshold: 0.85,
        offsetX: 0,
        offsetY: 0,
      },
    ])

  const addScreen = (x: number, y: number) =>
    writePoints([...points, { mode: 'screen', x, y, w: 0, h: 0, threshold: 0.85, offsetX: 0, offsetY: 0 }])

  const movePoint = (i: number, x: number, y: number) =>
    writePoints(points.map((p, idx) => (idx === i ? { ...p, x, y } : p)))

  const recrop = (i: number) =>
    writePoints(
      points.map((p, idx) =>
        idx === i && p.mode === 'image' ? { ...p, template: cropTemplate(p.x, p.y, p.w, p.h) } : p,
      ),
    )

  const removePoint = (i: number) => writePoints(points.filter((_, idx) => idx !== i))

  const setField = (i: number, patch: Partial<SwipePoint>) => {
    writePoints(
      points.map((p, idx) => {
        if (idx !== i) return p
        const merged = { ...p, ...patch }
        // Switching a fixed point to find-image: capture a default box around it.
        if (patch.mode === 'image' && p.mode === 'screen') {
          merged.w = merged.w || 90
          merged.h = merged.h || 40
          merged.template = cropTemplate(merged.x, merged.y, merged.w, merged.h)
        }
        return merged
      }),
    )
  }

  const onPick = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = String(reader.result)
      const img = new Image()
      img.onload = () =>
        updateConfigMany(node.id, {
          screenshotData: dataUrl,
          shotW: img.naturalWidth,
          shotH: img.naturalHeight,
          points: [],
          durations: [],
        })
      img.src = dataUrl
    }
    reader.readAsDataURL(file)
  }

  if (!src) {
    return (
      <>
        <button type="button" className="fp-swipe-drop" onClick={() => fileRef.current?.click()}>
          <ImagePlus size={18} />
          <span>上传整屏截图，然后在图上框选 / 点击标出滑动路径</span>
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="fp-hidden" onChange={onPick} />
      </>
    )
  }

  const stage = (
    <SwipeStage
      src={src}
      shotW={shotW}
      shotH={shotH}
      points={points}
      onAddImage={addImage}
      onAddScreen={addScreen}
      onMove={movePoint}
      onMoveEnd={recrop}
      onRemove={removePoint}
    />
  )

  return (
    <div className="fp-swipe">
      <img ref={cropImgRef} src={src} alt="" className="fp-hidden" />
      {stage}

      <div className="fp-swipe-toolbar">
        <button type="button" className="fp-btn fp-btn-ghost" onClick={() => setZoom(true)}>
          <Maximize2 size={14} /> 放大预览
        </button>
        <button type="button" className="fp-btn fp-btn-ghost" onClick={() => fileRef.current?.click()}>
          更换截图
        </button>
        {points.length > 0 && (
          <button type="button" className="fp-btn fp-btn-ghost" onClick={() => writePoints([])}>
            <Trash2 size={14} /> 清除点
          </button>
        )}
        <input ref={fileRef} type="file" accept="image/*" className="fp-hidden" onChange={onPick} />
      </div>

      <div className="fp-swipe-hint">
        <b>拖一个框</b> = 按图查找的点（框住要抓/放的东西，运行时在屏幕上找到它）；<b>单击</b> = 固定位置的点。
        拖动序号可移动，双击删除。运行时从点 1 按住依次滑到末点松开。
      </div>

      <label className="fp-field">
        <span className="fp-field-label">鼠标键</span>
        <select
          className="fp-input"
          value={String(config.button ?? 'left')}
          onChange={(e) => updateConfig(node.id, 'button', e.target.value)}
        >
          <option value="left">左键</option>
          <option value="right">右键</option>
        </select>
      </label>

      {points.map((p, i) => (
        <div className="fp-swipe-pt" key={i}>
          <div className="fp-swipe-pt-head">
            <span className="fp-swipe-pt-no">{i + 1}</span>
            <div className="fp-segment fp-segment-2 fp-swipe-pt-mode">
              <button
                type="button"
                className={`fp-segment-item${p.mode === 'image' ? ' is-active' : ''}`}
                onClick={() => setField(i, { mode: 'image' })}
              >
                按图查找
              </button>
              <button
                type="button"
                className={`fp-segment-item${p.mode === 'screen' ? ' is-active' : ''}`}
                onClick={() => setField(i, { mode: 'screen' })}
              >
                固定位置
              </button>
            </div>
            {p.mode === 'image' && p.template && (
              <img className="fp-swipe-pt-thumb" src={p.template} alt="" draggable={false} />
            )}
          </div>
          {p.mode === 'image' && (
            <>
              <div className="fp-field-label">匹配精度 {Math.round(p.threshold * 100)}%</div>
              <input
                className="fp-range"
                type="range"
                min={0.5}
                max={1}
                step={0.01}
                value={p.threshold}
                onChange={(e) => setField(i, { threshold: Number(e.target.value) })}
              />
              <div className="fp-row">
                <label className="fp-field">
                  <span className="fp-field-label">X 偏移</span>
                  <input className="fp-input" type="number" value={p.offsetX} onChange={(e) => setField(i, { offsetX: Number(e.target.value) })} />
                </label>
                <label className="fp-field">
                  <span className="fp-field-label">Y 偏移</span>
                  <input className="fp-input" type="number" value={p.offsetY} onChange={(e) => setField(i, { offsetY: Number(e.target.value) })} />
                </label>
              </div>
            </>
          )}
        </div>
      ))}

      {points.length >= 2 && (
        <div className="fp-swipe-segs">
          <span className="fp-field-label">每段滑动时长（秒）</span>
          {points.slice(1).map((_, i) => (
            <div className="fp-swipe-seg" key={i}>
              <span>
                {i + 1} → {i + 2}
              </span>
              <input
                type="number"
                min={0}
                step={0.1}
                value={Number(durations[i] ?? 0.3)}
                onChange={(e) => {
                  const next = adjustDurations(durations, points.length - 1)
                  next[i] = Math.max(0, Number(e.target.value))
                  updateConfig(node.id, 'durations', next)
                }}
              />
            </div>
          ))}
        </div>
      )}

      {zoom && (
        <div className="fp-swipe-overlay" onClick={() => setZoom(false)}>
          <div className="fp-swipe-overlay-inner" onClick={(e) => e.stopPropagation()}>
            <div className="fp-swipe-toolbar">
              <button type="button" className="fp-btn fp-btn-ghost" onClick={() => setZoom(false)}>
                <X size={14} /> 关闭
              </button>
              {points.length > 0 && (
                <button type="button" className="fp-btn fp-btn-ghost" onClick={() => writePoints([])}>
                  <Trash2 size={14} /> 清除点
                </button>
              )}
            </div>
            <SwipeStage
              src={src}
              shotW={shotW}
              shotH={shotH}
              points={points}
              onAddImage={addImage}
              onAddScreen={addScreen}
              onMove={movePoint}
              onMoveEnd={recrop}
              onRemove={removePoint}
            />
          </div>
        </div>
      )}
    </div>
  )
}

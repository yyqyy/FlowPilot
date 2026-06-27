import { useEffect, useRef, useState } from 'react'
import { ImagePlus, Maximize2, Trash2, X } from 'lucide-react'

import { useStore, type FlowNode } from '../store'

interface Point {
  x: number
  y: number
}

const clamp = (v: number, max: number) => Math.max(0, Math.min(max, v))

function adjustDurations(durations: number[], segments: number): number[] {
  const out = durations.slice(0, Math.max(0, segments))
  while (out.length < segments) out.push(0.3)
  return out
}

/** The clickable screenshot with numbered, draggable points and a path line.
 *  Coordinates are stored in screenshot-pixel space (shotW × shotH). */
function Stage({
  src,
  shotW,
  shotH,
  points,
  onAdd,
  onMove,
  onRemove,
}: {
  src: string
  shotW: number
  shotH: number
  points: Point[]
  onAdd: (x: number, y: number) => void
  onMove: (index: number, x: number, y: number) => void
  onRemove: (index: number) => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [drag, setDrag] = useState<number | null>(null)

  const toImage = (clientX: number, clientY: number): Point => {
    const r = ref.current!.getBoundingClientRect()
    return {
      x: clamp(Math.round(((clientX - r.left) / r.width) * shotW), shotW),
      y: clamp(Math.round(((clientY - r.top) / r.height) * shotH), shotH),
    }
  }

  useEffect(() => {
    if (drag === null) return
    const move = (e: MouseEvent) => {
      const p = toImage(e.clientX, e.clientY)
      onMove(drag, p.x, p.y)
    }
    const up = () => setDrag(null)
    window.addEventListener('mousemove', move)
    window.addEventListener('mouseup', up)
    return () => {
      window.removeEventListener('mousemove', move)
      window.removeEventListener('mouseup', up)
    }
  }, [drag]) // eslint-disable-line react-hooks/exhaustive-deps

  const onStageClick = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).classList.contains('fp-swipe-point')) return
    const p = toImage(e.clientX, e.clientY)
    onAdd(p.x, p.y)
  }

  const safeW = shotW || 1
  const safeH = shotH || 1

  return (
    <div className="fp-swipe-stage" ref={ref} onClick={onStageClick}>
      <img src={src} alt="" draggable={false} />
      {points.length >= 2 && (
        <svg className="fp-swipe-line" viewBox={`0 0 ${safeW} ${safeH}`} preserveAspectRatio="none">
          <polyline
            points={points.map((p) => `${p.x},${p.y}`).join(' ')}
            fill="none"
            stroke="#38bdf8"
            strokeWidth={Math.max(2, safeW / 240)}
            strokeLinejoin="round"
            strokeLinecap="round"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      )}
      {points.map((p, i) => (
        <div
          key={i}
          className="fp-swipe-point"
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
      ))}
    </div>
  )
}

export function SwipeEditor({ node }: { node: FlowNode }) {
  const fileRef = useRef<HTMLInputElement>(null)
  const updateConfig = useStore((s) => s.updateConfig)
  const updateConfigMany = useStore((s) => s.updateConfigMany)
  const [zoom, setZoom] = useState(false)

  const config = node.data.config
  const src = String(config.screenshotData ?? '')
  const shotW = Number(config.shotW ?? 0)
  const shotH = Number(config.shotH ?? 0)
  const points = (Array.isArray(config.points) ? config.points : []) as Point[]
  const durations = (Array.isArray(config.durations) ? config.durations : []) as number[]

  const setPoints = (next: Point[]) =>
    updateConfigMany(node.id, {
      points: next,
      durations: adjustDurations(durations, next.length - 1),
    })

  const addPoint = (x: number, y: number) => setPoints([...points, { x, y }])
  const movePoint = (i: number, x: number, y: number) =>
    setPoints(points.map((p, idx) => (idx === i ? { x, y } : p)))
  const removePoint = (i: number) => setPoints(points.filter((_, idx) => idx !== i))

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
          <span>上传整屏截图，然后在图上按顺序点出滑动路径</span>
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="fp-hidden" onChange={onPick} />
      </>
    )
  }

  const stage = (
    <Stage
      src={src}
      shotW={shotW}
      shotH={shotH}
      points={points}
      onAdd={addPoint}
      onMove={movePoint}
      onRemove={removePoint}
    />
  )

  return (
    <div className="fp-swipe">
      {stage}

      <div className="fp-swipe-toolbar">
        <button type="button" className="fp-btn fp-btn-ghost" onClick={() => setZoom(true)}>
          <Maximize2 size={14} /> 放大预览
        </button>
        <button type="button" className="fp-btn fp-btn-ghost" onClick={() => fileRef.current?.click()}>
          更换截图
        </button>
        {points.length > 0 && (
          <button type="button" className="fp-btn fp-btn-ghost" onClick={() => setPoints([])}>
            <Trash2 size={14} /> 清除点
          </button>
        )}
        <input ref={fileRef} type="file" accept="image/*" className="fp-hidden" onChange={onPick} />
      </div>

      <div className="fp-swipe-hint">
        在图上单击添加点（按 1→2→3 顺序），拖动可移动，双击删除。运行时从点 1 按住依次滑到末点松开。
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
                <button type="button" className="fp-btn fp-btn-ghost" onClick={() => setPoints([])}>
                  <Trash2 size={14} /> 清除点
                </button>
              )}
            </div>
            <Stage
              src={src}
              shotW={shotW}
              shotH={shotH}
              points={points}
              onAdd={addPoint}
              onMove={movePoint}
              onRemove={removePoint}
            />
          </div>
        </div>
      )}
    </div>
  )
}

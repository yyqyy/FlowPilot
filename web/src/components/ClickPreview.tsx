import { useState } from 'react'

// Shows the template image with a red dot at the click point (center + offset),
// so you can see exactly where the click will land. The dot moves live as the
// offset changes. Percentages map onto the image because the <img> keeps its
// aspect ratio (no object-fit letterboxing).
export function ClickPreview({
  src,
  offsetX,
  offsetY,
  variant,
}: {
  src: string
  offsetX: number
  offsetY: number
  variant: 'node' | 'inspector'
}) {
  const [dim, setDim] = useState<{ w: number; h: number } | null>(null)
  const clamp = (v: number) => Math.max(2, Math.min(98, v))
  const left = dim ? clamp((0.5 + offsetX / dim.w) * 100) : 50
  const top = dim ? clamp((0.5 + offsetY / dim.h) * 100) : 50

  return (
    <div className={`fp-clickprev fp-clickprev-${variant}`}>
      <img
        src={src}
        alt=""
        draggable={false}
        onLoad={(e) => setDim({ w: e.currentTarget.naturalWidth, h: e.currentTarget.naturalHeight })}
      />
      <span className="fp-clickdot" style={{ left: `${left}%`, top: `${top}%` }} />
    </div>
  )
}

import { Play, Plus, Square, Trash2 } from 'lucide-react'

import { useStore } from '../store'
import { TRIGGER_LABELS } from '../types'

export function TaskList() {
  const tasks = useStore((s) => s.tasks)
  const currentId = useStore((s) => s.currentId)
  const running = useStore((s) => s.running)
  const selectTask = useStore((s) => s.selectTask)
  const createTask = useStore((s) => s.createTask)
  const deleteTask = useStore((s) => s.deleteTask)
  const runTask = useStore((s) => s.runTask)
  const stopTask = useStore((s) => s.stopTask)

  return (
    <aside className="fp-tasklist">
      <div className="fp-tasklist-head">
        <span>任务</span>
        <button type="button" className="fp-icon-btn" title="新建任务" onClick={() => createTask()}>
          <Plus size={16} />
        </button>
      </div>

      <div className="fp-tasklist-scroll">
        {tasks.length === 0 && <div className="fp-tasklist-empty">还没有任务，点 + 新建一个。</div>}
        {tasks.map((task) => {
          const isRunning = running.includes(task.id)
          return (
            <div
              key={task.id}
              className={`fp-task${task.id === currentId ? ' is-active' : ''}`}
              onClick={() => selectTask(task.id)}
            >
              <button
                type="button"
                className={`fp-task-run${isRunning ? ' is-running' : ''}`}
                title={isRunning ? '停止' : '运行'}
                onClick={(e) => {
                  e.stopPropagation()
                  isRunning ? stopTask(task.id) : runTask(task.id)
                }}
              >
                {isRunning ? <Square size={13} /> : <Play size={13} />}
              </button>
              <div className="fp-task-info">
                <span className="fp-task-name">{task.name}</span>
                <span className="fp-task-meta">
                  {isRunning ? (
                    <span className="fp-task-running">运行中</span>
                  ) : (
                    TRIGGER_LABELS[task.trigger_mode]
                  )}
                  {task.hotkey && <span className="fp-kbd">{task.hotkey}</span>}
                </span>
              </div>
              <button
                type="button"
                className="fp-task-del"
                title="删除任务"
                onClick={(e) => {
                  e.stopPropagation()
                  deleteTask(task.id)
                }}
              >
                <Trash2 size={14} />
              </button>
            </div>
          )
        })}
      </div>
    </aside>
  )
}

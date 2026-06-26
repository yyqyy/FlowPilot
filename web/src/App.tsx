import { useEffect } from 'react'
import { ReactFlowProvider } from '@xyflow/react'

import { FlowCanvas } from './components/FlowCanvas'
import { Inspector } from './components/Inspector'
import { Palette } from './components/Palette'
import { TaskList } from './components/TaskList'
import { Toolbar } from './components/Toolbar'
import { useStore } from './store'

export default function App() {
  const init = useStore((s) => s.init)
  const refreshStatus = useStore((s) => s.refreshStatus)

  useEffect(() => {
    init()
    const timer = setInterval(() => refreshStatus(), 1200)
    return () => clearInterval(timer)
  }, [init, refreshStatus])

  return (
    <ReactFlowProvider>
      <div className="fp-app">
        <Toolbar />
        <div className="fp-main">
          <div className="fp-side">
            <TaskList />
            <Palette />
          </div>
          <FlowCanvas />
          <Inspector />
        </div>
      </div>
    </ReactFlowProvider>
  )
}

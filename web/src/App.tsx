import { ReactFlowProvider } from '@xyflow/react'

import { FlowCanvas } from './components/FlowCanvas'
import { Inspector } from './components/Inspector'
import { Palette } from './components/Palette'
import { Toolbar } from './components/Toolbar'

export default function App() {
  return (
    <ReactFlowProvider>
      <div className="fp-app">
        <Toolbar />
        <div className="fp-main">
          <Palette />
          <FlowCanvas />
          <Inspector />
        </div>
      </div>
    </ReactFlowProvider>
  )
}

import React from 'react'
import WorkflowEditor from './pages/WorkflowEditor'
import { Toaster } from '@/components/ui/toaster'

function App() {
  return (
    <div className="min-h-screen bg-background">
      <WorkflowEditor />
      <Toaster />
    </div>
  )
}

export default App
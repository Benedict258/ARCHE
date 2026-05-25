import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import AppPage from './pages/AppPage'
import SDK from './pages/SDK'
import '../UI-Guilde/index.css'
import './styles.css'

function Root(){
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing/>} />
        <Route path="/task-a" element={<AppPage mode="taskA"/>} />
        <Route path="/task-b" element={<AppPage mode="taskB"/>} />
        <Route path="/app" element={<Navigate to="/task-b" replace />} />
        <Route path="/sdk" element={<SDK/>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

createRoot(document.getElementById('root')).render(<Root />)

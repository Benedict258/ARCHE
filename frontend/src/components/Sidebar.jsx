import React from 'react'
import { NavLink } from 'react-router-dom'
import { docsUrl } from '../lib/api'

const Sidebar = ()=>{
  const linkClass = ({isActive}) => isActive ? 'btn nav-btn active' : 'btn nav-btn'
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon" />
        <div className="logo-text">
          <div className="logo-title">ARCHE v1.0</div>
          <div className="logo-subtitle">Active Reasoning</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink to="/" className={linkClass}>Home</NavLink>
        <NavLink to="/task-a" className={linkClass}>Task A</NavLink>
        <NavLink to="/task-b" className={linkClass}>Task B</NavLink>
        <NavLink to="/sdk" className={linkClass}>SDK</NavLink>
      </nav>

      <div className="sidebar-footer">
        <a className="btn ghost" href={docsUrl} target="_blank" rel="noreferrer">Docs</a>
      </div>
    </aside>
  )
}

export default Sidebar

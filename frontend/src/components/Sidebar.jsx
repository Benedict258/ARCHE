import React from 'react'
import { NavLink } from 'react-router-dom'
import { docsUrl } from '../lib/api'

const Sidebar = ()=>{
  const linkClass = ({isActive}) => isActive ? 'btn nav-btn active' : 'btn nav-btn'
  return (
    <aside className="sidebar" style={{width:240,padding:20,borderRight:'1px solid rgba(255,255,255,0.03)'}}>
      <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:18}}>
        <div style={{width:36,height:36,background:'var(--primary)',borderRadius:8}} />
        <div>
          <div style={{fontWeight:700}}>ARCHE v1.0</div>
          <div className="muted" style={{fontSize:12}}>Active Reasoning</div>
        </div>
      </div>

      <nav style={{display:'flex',flexDirection:'column',gap:8}}>
        <NavLink to="/" className={linkClass}>Home</NavLink>
        <NavLink to="/task-a" className={linkClass}>Task A</NavLink>
        <NavLink to="/task-b" className={linkClass}>Task B</NavLink>
        <NavLink to="/sdk" className={linkClass}>SDK</NavLink>
      </nav>

      <div style={{marginTop:20}}>
        <a className="btn ghost" href={docsUrl} target="_blank" rel="noreferrer">Docs</a>
      </div>
    </aside>
  )
}

export default Sidebar

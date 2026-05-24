import React from 'react'
import { NavLink } from 'react-router-dom'

const TopNav = ()=>{
  const linkClass = ({isActive}) => isActive ? 'muted active' : 'muted'
  return (
    <div className="topnav" style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'10px 20px',gap:12}}>
      <div style={{display:'flex',alignItems:'center',gap:12}}>
        <div style={{fontWeight:700,color:'var(--primary-foreground)'}}>ARCHE</div>
        <nav style={{display:'flex',gap:14}}>
          <NavLink to="/" className={linkClass}>Dashboard</NavLink>
          <NavLink to="/app" className={linkClass}>Simulation</NavLink>
          <NavLink to="/app" className={linkClass}>Recommendation</NavLink>
          <NavLink to="/sdk" className={linkClass}>SDK</NavLink>
        </nav>
      </div>

      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <a className="btn" href="/docs" target="_blank" rel="noreferrer">Open API</a>
        <button className="btn primary">Deploy Agent</button>
      </div>
    </div>
  )
}

export default TopNav

import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { docsUrl } from '../lib/api'

const TopNav = ()=>{
  const navigate = useNavigate()
  const linkClass = ({isActive}) => isActive ? 'muted nav-link active' : 'muted nav-link'

  function goBack(){
    if(window.history.length > 1){
      navigate(-1)
      return
    }
    navigate('/')
  }

  return (
    <div className="topnav" style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'10px 20px',gap:12}}>
      <div style={{display:'flex',alignItems:'center',gap:12}}>
        <button className="btn ghost" onClick={goBack}>Back</button>
        <div style={{fontWeight:700,color:'var(--primary-foreground)'}}>ARCHE</div>
        <nav style={{display:'flex',gap:14}}>
          <NavLink to="/" className={linkClass}>Dashboard</NavLink>
          <NavLink to="/task-a" className={linkClass}>Task A</NavLink>
          <NavLink to="/task-b" className={linkClass}>Task B</NavLink>
          <NavLink to="/sdk" className={linkClass}>SDK</NavLink>
        </nav>
      </div>

      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <a className="btn" href={docsUrl} target="_blank" rel="noreferrer">Open API</a>
        <a className="btn primary" href="https://vercel.com/new" target="_blank" rel="noreferrer">Deploy</a>
      </div>
    </div>
  )
}

export default TopNav

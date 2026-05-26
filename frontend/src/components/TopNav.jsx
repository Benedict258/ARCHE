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
    <div className="topnav">
      <div className="topnav-inner">
        <div className="topnav-left">
          <button className="btn ghost" onClick={goBack}>Back</button>
          <div className="topnav-brand">ARCHE</div>
          <nav className="topnav-nav">
            <NavLink to="/sdk" className={linkClass}>SDK</NavLink>
            <a className={linkClass({isActive:false})} href={docsUrl} target="_blank" rel="noreferrer">API</a>
            <NavLink to="/task-b" className={linkClass}>Try Demo</NavLink>
          </nav>
        </div>


        <div className="topnav-right">
          <a className="btn" href={docsUrl} target="_blank" rel="noreferrer">Open API</a>
          <a className="btn primary" href="https://vercel.com/new" target="_blank" rel="noreferrer">Deploy</a>
        </div>
      </div>
    </div>
  )
}

export default TopNav

import React from 'react'
import { useNavigate } from 'react-router-dom'
import TopNav from '../components/TopNav'
import Sidebar from '../components/Sidebar'
import Card from '../components/Card'
import Icon from '../components/Icon'

const Landing = ()=>{
  const nav = useNavigate()
  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <div style={{flex:1}}>
        <TopNav />

        <main style={{padding:24}}>
          <section className="hero" style={{display:'flex',gap:20,alignItems:'center'}}>
            <div style={{flex:1}}>
              <h1 className="title">ARCHE</h1>
              <p className="subtitle">Simulate users. Recommend what they need. Explain why.</p>
              <div className="cta-row">
                <button className="btn primary" onClick={()=>nav('/app')}>Open App</button>
                <a className="btn ghost" href="/docs" target="_blank" rel="noreferrer">Open API (Swagger)</a>
                <button className="btn" onClick={()=>nav('/sdk')}>SDK</button>
              </div>
            </div>

            <div style={{width:480}}>
              <div className="card" style={{height:220,display:'flex',alignItems:'center',justifyContent:'center'}}>
                <div>
                  <div className="hero-big">ARCHE<br/>User Modeling & Recommendation</div>
                  <div className="muted-small" style={{marginTop:8}}>Simulate users, generate explainable recommendations, and integrate live evidence — demo mode.</div>
                </div>
              </div>
            </div>
          </section>

          <section className="features" style={{marginTop:26}}>
            <div className="card-grid">
              <Card>
                <div style={{display:'flex',gap:12,alignItems:'center'}}>
                  <Icon name="ingest" />
                  <div>
                    <div style={{fontWeight:600}}>Robust Ingest</div>
                    <div className="muted-small">Accepts messy input, repairs it, and stores signals.</div>
                  </div>
                </div>
              </Card>

              <Card>
                <div style={{display:'flex',gap:12,alignItems:'center'}}>
                  <Icon name="llm" />
                  <div>
                    <div style={{fontWeight:600}}>LLM Simulation</div>
                    <div className="muted-small">Simulates user intent to personalize first-session experiences.</div>
                  </div>
                </div>
              </Card>

              <Card>
                <div style={{display:'flex',gap:12,alignItems:'center'}}>
                  <Icon name="explain" />
                  <div>
                    <div style={{fontWeight:600}}>Explainable Results</div>
                    <div className="muted-small">Every recommendation includes a short, verifiable explanation.</div>
                  </div>
                </div>
              </Card>
            </div>
          </section>

          <footer className="footer">Light-mode demo • Simple, responsive UI</footer>
        </main>
      </div>
    </div>
  )
}

export default Landing

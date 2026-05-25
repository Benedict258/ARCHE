import React from 'react'
import { useNavigate } from 'react-router-dom'
import TopNav from '../components/TopNav'
import Sidebar from '../components/Sidebar'
import Icon from '../components/Icon'
import { docsUrl } from '../lib/api'

const Landing = ()=>{
  const nav = useNavigate()

  return (
    <div className="app-shell" style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <div className="main-shell" style={{flex:1}}>
        <TopNav />

        <main className="page landing-page">
          <section className="hero landing-hero">
            <div className="landing-hero-copy">
              <h1 className="title">ARCHE</h1>
              <p className="subtitle">Behavioral intelligence platform for simulated user modeling and explainable recommendation workflows.</p>
              <p className="landing-lead">ARCHE ingests messy user intent, translates it into structured decision signals, and returns deterministic outputs for both product simulation and recommendation ranking.</p>
              <div className="core-actions">
                <button className="btn primary" onClick={()=>nav('/task-a')}>User Model (Task A)</button>
                <button className="btn primary" onClick={()=>nav('/task-b')}>Recommendation (Task B)</button>
                <a className="btn ghost" href={docsUrl} target="_blank" rel="noreferrer">Open API-Swagger</a>
                <button className="btn" onClick={()=>nav('/sdk')}>SDK</button>
              </div>
            </div>

            <div className="card landing-highlight">
              <div className="hero-big">How ARCHE Works</div>
              <ol className="how-list">
                <li>
                  <strong>Input Layer</strong>
                  <span>Accepts normal text, JSON, or entry form payloads.</span>
                </li>
                <li>
                  <strong>Translation Layer</strong>
                  <span>Repairs or transforms input into request-safe schema payloads.</span>
                </li>
                <li>
                  <strong>Reasoning Layer</strong>
                  <span>Runs simulation and recommendation logic using contextual memory.</span>
                </li>
                <li>
                  <strong>Output Layer</strong>
                  <span>Returns human-readable text or JSON depending selected mode.</span>
                </li>
              </ol>
            </div>
          </section>

          <section className="landing-sections">
            <article className="card section-card">
              <h3>Platform Overview</h3>
              <p className="muted">ARCHE is designed to show how product teams can move from vague user signals to explainable decisions in a single pipeline.</p>
              <div className="feature-row">
                <div className="feature-item">
                  <Icon name="ingest" />
                  <div>
                    <h4>Robust Input Handling</h4>
                    <p className="muted-small">Input repair accepts malformed or natural language requests and maps them to valid API contracts.</p>
                  </div>
                </div>
                <div className="feature-item">
                  <Icon name="llm" />
                  <div>
                    <h4>User Behavior Simulation</h4>
                    <p className="muted-small">Task A predicts a realistic user response and supports plain-text output mode for direct consumption.</p>
                  </div>
                </div>
                <div className="feature-item">
                  <Icon name="explain" />
                  <div>
                    <h4>Explainable Recommendations</h4>
                    <p className="muted-small">Task B generates ranked outputs and traceable explanations for why each recommendation was selected.</p>
                  </div>
                </div>
              </div>
            </article>

            <article className="card section-card">
              <h3>Deployment Notes</h3>
              <ul className="bullet-list muted">
                <li>Use the task pages to test plain text, JSON, and entry-based request modes.</li>
                <li>Swagger remains the contract source for backend validation and quick testing.</li>
                <li>The SDK page includes copy-ready integration examples for local and production.</li>
              </ul>
              <div className="cta-row" style={{justifyContent:'flex-start'}}>
                <button className="btn" onClick={()=>nav('/sdk')}>Read SDK Guide</button>
                <button className="btn" onClick={()=>nav('/task-b')}>Try Recommendation Flow</button>
              </div>
            </article>
          </section>

          <footer className="footer">ARCHE Demo Platform - Input translation, simulation, recommendation, explainability</footer>
        </main>
      </div>
    </div>
  )
}

export default Landing

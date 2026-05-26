import React from 'react'
import { useNavigate } from 'react-router-dom'
import { docsUrl } from '../lib/api'

const Landing = () => {
  const nav = useNavigate()

  return (
    <div className="landing-full">
      <header className="landing-top">
        <div className="landing-top-inner">
          <div className="landing-brand">ARCHE</div>
          <nav className="landing-nav">
            <button className="btn ghost" onClick={()=>nav('/sdk')}>SDK</button>
            <a className="btn ghost" href={docsUrl} target="_blank" rel="noreferrer">API</a>
            <button className="btn" onClick={()=>nav('/task-b')}>Try Demo</button>
          </nav>
        </div>
      </header>

      <main>
        <section className="landing-screen screen-hero">
          <div className="hero-inner">
            <h1 className="hero-title">ARCHE</h1>
            <p className="hero-sub">Behavioral intelligence for simulated user models and explainable recommendations.</p>
            <p className="hero-lead">Turn messy user signals into deterministic, explainable outputs for testing and production.</p>
            <div className="hero-ctas">
              <button className="btn primary" onClick={() => nav('/task-a')}>Run User Model (Task A)</button>
              <button className="btn primary" onClick={() => nav('/task-b')}>Run Recommendation (Task B)</button>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-simulation">
          <div className="simulation-inner card">
            <h2>Behavioral Simulation: How ARCHE Works</h2>
            <p>At the core of ARCHE is a <strong>behavioral simulation engine</strong> that learns a user's decision-making patterns from their review history.</p>
            <div className="sim-steps">
              <div className="sim-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <h4>Extract Behavioral Patterns</h4>
                  <p>From your review history, we detect your <strong>decision drivers</strong>: Are you price-conscious? Quality-first? Value-seeking? Do you write formally or in Nigerian Pidgin?</p>
                </div>
              </div>
              <div className="sim-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <h4>Build a Deterministic Snapshot</h4>
                  <p>Your patterns become a <strong>behavioral snapshot</strong>—a structured representation of your tastes. Not a vector; not a black box. Every decision is traceable.</p>
                </div>
              </div>
              <div className="sim-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <h4>Apply Context & Reasoning</h4>
                  <p>When you review a new item or ask for recommendations, we inject <strong>context signals</strong> (time of day, location, occasion) and reason forward using your behavioral profile.</p>
                </div>
              </div>
              <div className="sim-step">
                <div className="step-number">4</div>
                <div className="step-content">
                  <h4>Generate Explainable Output</h4>
                  <p>Every prediction includes a <strong>basis statement</strong> explaining why—"Matches your interest in X" or "Price tier aligns with your typical range"—so you know exactly how the system arrived at its answer.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-concepts">
          <div className="concepts-inner card">
            <h2>Key Concepts: Understanding ARCHE Outputs</h2>
            <div className="concept-grid">
              <div className="concept">
                <h4>Behavioral Basis</h4>
                <p><strong>Shows the foundation:</strong> "Detected formal_english register with 3 prior reviews; simulation basis historical_memory; top affinities [food, electronics]"</p>
              </div>
              <div className="concept">
                <h4>Recommendation Type</h4>
                <p><strong>Precision:</strong> Direct match (60%)</p>
                <p><strong>Adjacent:</strong> Related categories (25%).</p>
                <p><strong>Discovery:</strong> New categories (15%)</p>
              </div>
              <div className="concept">
                <h4>Exploration Factor</h4>
                <p><strong>inline_history:</strong> Based on your data.</p>
                <p><strong>cold_start_prior:</strong> Cohort defaults.</p>
                <p><strong>context_signal:</strong> Time/location adjusted.</p>
              </div>
              <div className="concept">
                <h4>Explanation</h4>
                <p>Real reasoning: "Matches your interest in nigerian_cuisine"—not cryptic internal state codes.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-how">
          <div className="how-inner card">
            <h2>How it works</h2>
            <ol>
              <li><strong>Input Layer</strong> — Accepts normal language, JSON, or form entries; repairs malformed input.</li>
              <li><strong>Translation</strong> — Converts inputs to schema-safe payloads for the API.</li>
              <li><strong>Reasoning</strong> — Simulation and ranking agents produce predictions and scores.</li>
              <li><strong>Output</strong> — Returns human-readable text and structured JSON with explanations.</li>
            </ol>
          </div>
        </section>

        <section className="landing-screen screen-stack">
          <div className="stack-inner card">
            <h2>Stack & Techniques</h2>
            <p className="muted">FastAPI backend, lightweight orchestrator agents, deterministic privacy abstraction, and a Vite+React frontend. Supports input repair, simulation, ranking, and explainability traces.</p>
            <div className="tech-grid">
              <div className="tech">FastAPI</div>
              <div className="tech">Pydantic</div>
              <div className="tech">React + Vite</div>
              <div className="tech">LLM Agents (local orchestration)</div>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-api card">
          <h2>API & SDK</h2>
          <p className="muted">Use the API endpoints for `Task A` (simulate-review) and `Task B` (recommend). The SDK page contains usage examples and code snippets for local and production integration.</p>
          <div className="cta-row">
            <a className="btn primary" href={docsUrl} target="_blank" rel="noreferrer">Open API Swagger</a>
            <button className="btn" onClick={()=>nav('/sdk')}>SDK Guide</button>
          </div>
        </section>
      </main>
    </div>
  )
}

export default Landing

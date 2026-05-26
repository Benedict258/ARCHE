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
            <p className="hero-sub">The intelligence layer that simulates <strong>who</strong> your customers are, recommends <strong>what</strong> they actually need, and explains exactly <strong>why</strong>.</p>
            <p className="hero-lead">Move beyond simple vectors. Simulate human decision-making with authentic linguistic registers and cultural calibration.</p>
            <div className="hero-ctas">
              <button className="btn primary" onClick={() => nav('/task-a')}>Simulate User Review (Task A)</button>
              <button className="btn primary" onClick={() => nav('/task-b')}>Predict Recommendation (Task B)</button>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-simulation">
          <div className="simulation-inner card">
            <h2>Behavioral Archetypes: Beyond the Persona</h2>
            <p>ARCHE doesn't just predict ratings; it simulates a user's <strong>cognitive state</strong>. Our engine reasons forward from historical behavior to model how a specific individual reacts to new items in real-time context.</p>
            <div className="sim-steps">
              <div className="sim-step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <h4>Linguistic Register Capture</h4>
                  <p>We detect decision drivers from history: Is the user an elite critic using corporate English, or a practical regular writing in <strong>Nigerian Pidgin</strong>?</p>
                </div>
              </div>
              <div className="sim-step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <h4>Contextual Reasoning</h4>
                  <p>Signals like <strong>Lagos Island traffic</strong>, power grid status, and time-of-day are injected into the user's brain-state to shift their decision criteria dynamically.</p>
                </div>
              </div>
              <div className="sim-step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <h4>Absolute Value Faithfulness</h4>
                  <p>Our <strong>Linguistic Blocklist</strong> and tone-locking guardrails ensure that elite personas stay refined, while casual personas stay authentic. No more persona drift.</p>
                </div>
              </div>
              <div className="sim-step">
                <div className="step-number">4</div>
                <div className="step-content">
                  <h4>Explainable Justification</h4>
                  <p>Every prediction includes a causal reasoning trace. We don't just give you a 3-star rating; we tell you <strong>exactly</strong> why the user felt the wattage was too high for their generator.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-concepts">
          <div className="concepts-inner card">
            <h2>The ARCHE Standard: Smart & Transparent</h2>
            <div className="concept-grid">
              <div className="concept">
                <h4>Sentiment-Rating Coherence</h4>
                <p><strong>Strict Guardrails:</strong> Our engine enforces mathematical alignment between numerical ratings and generated prose. A 2-star rating will <em>never</em> produce a 5-star review.</p>
              </div>
              <div className="concept">
                <h4>60/25/15 Discovery Split</h4>
                <p><strong>Anti-Bubble:</strong> Precision (60%), Adjacent Exploration (25%), and Discovery (15%) ensure users find what they need while being exposed to novel Nigerian options.</p>
              </div>
              <div className="concept">
                <h4>Privacy-by-Design</h4>
                <p><strong>Hash-and-Redact:</strong> Deterministic privacy layer ensures PII is redacted and tokens are hashed before any agentic reasoning occurs.</p>
              </div>
              <div className="concept">
                <h4>Live Web Enrichment</h4>
                <p><strong>Real-Time Signal:</strong> We blend your local catalog with live web evidence from the Serper API to provide the most current recommendations possible.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-stack">
          <div className="stack-inner card">
            <h2>Agentic Infrastructure</h2>
            <p className="muted">Built as enterprise infrastructure for African e-commerce. Scalable, modular, and grounded in real datasets.</p>
            <div className="tech-grid">
              <div className="tech">LangGraph Orchestration</div>
              <div className="tech">Groq (Llama 3.3 70B)</div>
              <div className="tech">FastAPI & Pydantic V2</div>
              <div className="tech">Local Vector Memory</div>
            </div>
          </div>
        </section>

        <section className="landing-screen screen-api card">
          <h2>Ready to Build?</h2>
          <p className="muted">Access the production-ready API or integrate using our lightweight SDK. ARCHE is designed to be the intelligence layer for the next generation of African digital products.</p>
          <div className="cta-row">
            <a className="btn primary" href={docsUrl} target="_blank" rel="noreferrer">Open API Swagger</a>
            <button className="btn" onClick={()=>nav('/sdk')}>Integration Guide</button>
          </div>
        </section>
      </main>

      <footer className="footer" style={{padding: '40px 20px', borderTop: '1px solid var(--border-color)'}}>
        <p>&copy; 2026 ARCHE Intelligence Layer • DSN x BCT LLM Agent Challenge</p>
      </footer>
    </div>
  )
}

export default Landing


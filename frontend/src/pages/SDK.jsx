import React from 'react'
import TopNav from '../components/TopNav'
import Sidebar from '../components/Sidebar'
import { docsUrl } from '../lib/api'

const INSTALL_SNIPPET = `python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt`

const SETUP_SNIPPET = `from sdk.client import ArcheClient

client = ArcheClient("http://127.0.0.1:8000")
health = await client.health()
print(health)`

const TASK_A_SNIPPET = `simulate_payload = {
  "user_token": "demo_user_001",
  "user_history": [],
  "item": {
    "name": "Dominos Pizza Lagos",
    "category": "fast_food",
    "price_tier": "mid",
    "attributes": {"delivery": True}
  },
  "context": {"time_of_day": "evening", "region": "Lagos"}
}

# HTTP endpoint: POST /v1/simulate-review`

const TASK_B_SNIPPET = `recommendation = await client.recommend(
  "demo_user_001",
  {"time_bucket": "evening", "entry_point": "web"},
  n=5,
)

first_id = recommendation.recommendations[0].recommendation_id
explanation = await client.explain("demo_user_001", first_id)
print(explanation)`

const SDK = ()=>{
  return (
    <div className="app-shell" style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <div className="main-shell" style={{flex:1}}>
        <TopNav />

        <main className="page sdk-page">
          <header className="hero small">
            <h2>ARCHE SDK Documentation</h2>
            <p>Local pre-deployment docs for integrating ARCHE API in Python workflows.</p>
            <div className="cta-row" style={{justifyContent:'center'}}>
              <a className="btn ghost" href={docsUrl} target="_blank" rel="noreferrer">Open Swagger</a>
              <a className="btn" href="https://github.com/Benedict258/ARCHE" target="_blank" rel="noreferrer">Repository</a>
            </div>
          </header>

          <section className="card section-card">
            <h3>1. Installation</h3>
            <pre className="response-output">{INSTALL_SNIPPET}</pre>
            <p className="muted-small">The SDK client is provided in <code>sdk/client.py</code>.</p>
          </section>

          <section className="card section-card">
            <h3>2. Basic Client Setup</h3>
            <pre className="response-output">{SETUP_SNIPPET}</pre>
          </section>

          <section className="card section-card">
            <h3>3. Task A Example - User Model</h3>
            <pre className="response-output">{TASK_A_SNIPPET}</pre>
          </section>

          <section className="card section-card">
            <h3>4. Task B Example - Recommendation + Explain</h3>
            <pre className="response-output">{TASK_B_SNIPPET}</pre>
          </section>

          <section className="card section-card">
            <h3>5. Integration Notes</h3>
            <ul className="bullet-list muted">
              <li>Use Task pages in this frontend to test payload translation modes before automation.</li>
              <li>Use <code>raw_input</code> with <code>output_format: "text"</code> when sending natural language.</li>
              <li>Use direct JSON payloads for strict integration and regression testing.</li>
              <li>When deployed, replace localhost base URL with your production API host.</li>
            </ul>
          </section>
        </main>
      </div>
    </div>
  )
}

export default SDK

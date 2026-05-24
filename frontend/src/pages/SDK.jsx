import React from 'react'

const SDK = ()=>{
  return (
    <div className="page small">
      <header className="hero small">
        <h2>ARCHE SDK</h2>
        <p>Lightweight Python SDK is included in the repository. This page will link SDK docs once deployed.</p>
      </header>

      <main className="content">
        <div className="panel">
          <h3>Quick Start (Python)</h3>
          <pre>
pip install -r requirements.txt
python -m sdk.client --help
          </pre>
          <p>When the SDK is deployed we'll update this page with examples and a hosted doc.</p>
        </div>
      </main>
    </div>
  )
}

export default SDK

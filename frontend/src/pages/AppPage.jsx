import React, { useMemo, useState } from 'react'
import TopNav from '../components/TopNav'
import Sidebar from '../components/Sidebar'
import { apiUrl } from '../lib/api'
import {
  buildTaskARequest,
  buildTaskBRecommendRequest,
  buildTaskBExplainRequest,
  formatResponseForDisplay,
} from '../lib/payloadLayer'

const SAMPLE_TASK_A_TEXT = 'User is a busy professional in Lagos who likes value meals. Please simulate how they would review a mid-priced fast food item tonight.'
const SAMPLE_TASK_B_TEXT = 'Recommend 5 dinner options for a user browsing from mobile in the evening. Prefer food category and return concise reasoning.'
const SAMPLE_TASK_A_JSON = JSON.stringify({
  user_token: 'demo_user_001',
  user_history: [
    {
      item_name: 'Chicken Republic Lekki',
      item_category: 'fast_food',
      rating: 4,
      review_text: 'The jollof was decent and delivery was fast.'
    }
  ],
  item: {
    name: 'Dominos Pizza Lagos',
    category: 'fast_food',
    price_tier: 'mid',
    attributes: { delivery: true }
  },
  context: { time_of_day: 'evening', region: 'Lagos' },
  output_format: 'json'
}, null, 2)

const SAMPLE_TASK_B_JSON = JSON.stringify({
  user_token: 'demo_user_001',
  context: { time_bucket: 'evening', entry_point: 'web' },
  n: 5,
  domain_filter: 'food',
  output_format: 'json'
}, null, 2)

const AppPage = ({mode='taskB'})=>{
  const isTaskA = mode === 'taskA'
  const [inputMode, setInputMode] = useState('text')
  const [loading, setLoading] = useState(false)
  const [responseRaw, setResponseRaw] = useState(null)
  const [responseText, setResponseText] = useState('')
  const [showFormatted, setShowFormatted] = useState(true)
  const [statusText, setStatusText] = useState('Idle')

  const [userToken, setUserToken] = useState('demo_user_001')
  const [recommendationId, setRecommendationId] = useState('')
  const [textInput, setTextInput] = useState(isTaskA ? SAMPLE_TASK_A_TEXT : SAMPLE_TASK_B_TEXT)
  const [jsonInput, setJsonInput] = useState(isTaskA ? SAMPLE_TASK_A_JSON : SAMPLE_TASK_B_JSON)
  const [entries, setEntries] = useState({
    reviewText: '',
    previousItemName: 'Chicken Republic Lekki',
    previousItemCategory: 'fast_food',
    previousRating: '4',
    itemName: 'Dominos Pizza Lagos',
    itemCategory: 'fast_food',
    priceTier: 'mid',
    timeOfDay: 'evening',
    region: 'Lagos',
    forcedRating: '',
    timeBucket: 'evening',
    entryPoint: 'web',
    domainFilter: 'food',
    itemPoolJson: '',
    n: '5',
    recommendationId: ''
  })

  const pageTitle = isTaskA ? 'User Model (Task A)' : 'Recommendation (Task B)'
  const pageSummary = isTaskA
    ? 'Test simulation using natural text, JSON payloads, or entry form mode.'
    : 'Test recommendation workflows with the same input translation layer and optional explanation requests.'

  const modeExplanation = useMemo(() => {
    if(inputMode === 'text'){
      return 'Normal text mode: frontend sends raw_input and requests formatted text output.'
    }
    if(inputMode === 'json'){
      return 'JSON mode: payload is passed directly to the endpoint.'
    }
    return 'Entries mode: form fields are translated into valid request JSON.'
  }, [inputMode])

  function updateEntry(key, value){
    setEntries(prev => ({...prev, [key]: value}))
  }

  async function postPayload(path, body){
    setLoading(true)
    setStatusText('Running request...')
    try{
      const r = await fetch(apiUrl(path), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(body)
      })

      const contentType = r.headers.get('content-type') || ''
      let payload
      if(contentType.includes('application/json')){
        payload = await r.json()
      }else{
        payload = await r.text()
      }

      if(!r.ok){
        const detail = typeof payload === 'string' ? payload : payload?.detail || payload?.error || 'Request failed'
        setStatusText(`Error (HTTP ${r.status})`)
        setResponseRaw(null)
        setResponseText(`Error: ${detail}`)
      }else{
        setStatusText('Success')
        setResponseRaw(payload)
        setResponseText(formatResponseForDisplay(payload))
      }
    }catch(error){
      setStatusText('Network error')
      setResponseRaw(null)
      setResponseText(`Error: ${error.message}`)
    }finally{
      setLoading(false)
    }
  }

  async function runPrimaryTask(){
    try{
      if(isTaskA){
        const payload = buildTaskARequest({
          inputMode,
          textInput,
          jsonInput,
          entries,
          userToken
        })
        await postPayload('/v1/simulate-review', payload)
      }else{
        const payload = buildTaskBRecommendRequest({
          inputMode,
          textInput,
          jsonInput,
          entries,
          userToken
        })
        await postPayload('/v1/recommend', payload)
      }
    }catch(error){
      setStatusText('Payload validation error')
      setResponseText(`Error: ${error.message}`)
    }
  }

  async function runExplain(){
    try{
      const payload = buildTaskBExplainRequest({
        inputMode,
        textInput,
        jsonInput,
        entries,
        userToken,
        recommendationId
      })
      if(!payload.recommendation_id){
        setStatusText('Validation error')
        setResponseText('Error: recommendation_id is required for explain requests.')
        return
      }
      await postPayload('/v1/explain', payload)
    }catch(error){
      setStatusText('Payload validation error')
      setResponseText(`Error: ${error.message}`)
    }
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="main-shell">
        <TopNav />

        <main className="page task-page">
          <header className="hero small task-hero">
            <h2>{pageTitle}</h2>
            <p>{pageSummary}</p>

            <div className="control-row">
              <label className="field">
                <span className="field-label">User Token</span>
                <input
                  className="input-control"
                  value={userToken}
                  onChange={(e)=>setUserToken(e.target.value)}
                  autoComplete="off"
                />
              </label>
            </div>
          </header>

          <section className="card translation-card">
            <h3>Input Translation Layer</h3>
            <p className="muted-small">{modeExplanation}</p>
            <div className="mode-switch">
              <button className={`btn ${inputMode === 'text' ? 'primary' : 'ghost'}`} onClick={()=>setInputMode('text')}>Normal Text</button>
              <button className={`btn ${inputMode === 'json' ? 'primary' : 'ghost'}`} onClick={()=>setInputMode('json')}>JSON</button>
              <button className={`btn ${inputMode === 'entries' ? 'primary' : 'ghost'}`} onClick={()=>setInputMode('entries')}>Entries</button>
            </div>

            <div style={{marginTop:12}}>
              <button className="btn primary" disabled={loading} onClick={runPrimaryTask}>
                {isTaskA ? 'Run User Model (Task A)' : 'Run Recommendation (Task B)'}
              </button>
            </div>

            {inputMode === 'text' && (
              <label className="field full-width">
                <span className="field-label">Natural Language Input</span>
                <textarea
                  className="text-area"
                  value={textInput}
                  onChange={(e)=>setTextInput(e.target.value)}
                  placeholder="Describe what you want in normal language"
                />
              </label>
            )}

            {inputMode === 'json' && (
              <label className="field full-width">
                <span className="field-label">JSON Payload</span>
                <textarea
                  className="text-area code"
                  value={jsonInput}
                  onChange={(e)=>setJsonInput(e.target.value)}
                  spellCheck={false}
                />
              </label>
            )}

            {inputMode === 'entries' && (
              <div className="entries-grid">
                {isTaskA ? (
                  <>
                    <label className="field"><span className="field-label">Previous Item</span><input className="input-control" value={entries.previousItemName} onChange={(e)=>updateEntry('previousItemName', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Previous Category</span><input className="input-control" value={entries.previousItemCategory} onChange={(e)=>updateEntry('previousItemCategory', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Previous Rating</span><input className="input-control" value={entries.previousRating} onChange={(e)=>updateEntry('previousRating', e.target.value)} /></label>
                    <label className="field"><span className="field-label">New Item Name</span><input className="input-control" value={entries.itemName} onChange={(e)=>updateEntry('itemName', e.target.value)} /></label>
                    <label className="field"><span className="field-label">New Item Category</span><input className="input-control" value={entries.itemCategory} onChange={(e)=>updateEntry('itemCategory', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Price Tier</span><input className="input-control" value={entries.priceTier} onChange={(e)=>updateEntry('priceTier', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Time of Day</span><input className="input-control" value={entries.timeOfDay} onChange={(e)=>updateEntry('timeOfDay', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Region</span><input className="input-control" value={entries.region} onChange={(e)=>updateEntry('region', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Forced Rating (1-5)</span><input className="input-control" placeholder="Optional" value={entries.forcedRating} onChange={(e)=>updateEntry('forcedRating', e.target.value)} /></label>
                    <label className="field full-width"><span className="field-label">Review History Text</span><textarea className="text-area" value={entries.reviewText} onChange={(e)=>updateEntry('reviewText', e.target.value)} /></label>
                  </>
                ) : (
                  <>
                    <label className="field"><span className="field-label">Domain Filter</span><input className="input-control" value={entries.domainFilter} onChange={(e)=>updateEntry('domainFilter', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Entry Point</span><input className="input-control" value={entries.entryPoint} onChange={(e)=>updateEntry('entryPoint', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Time Bucket</span><input className="input-control" value={entries.timeBucket} onChange={(e)=>updateEntry('timeBucket', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Result Count (n)</span><input className="input-control" value={entries.n} onChange={(e)=>updateEntry('n', e.target.value)} /></label>
                    <label className="field"><span className="field-label">Recommendation ID</span><input className="input-control" value={entries.recommendationId} onChange={(e)=>updateEntry('recommendationId', e.target.value)} /></label>
                    <label className="field full-width"><span className="field-label">Item Pool JSON (Optional)</span><textarea className="text-area code" placeholder='[{"item_name": "Item 1", "category": "food"}]' value={entries.itemPoolJson} onChange={(e)=>updateEntry('itemPoolJson', e.target.value)} /></label>
                  </>
                )}
              </div>
            )}
          </section>

          <section className="card response-card">
            <div className="response-head">
              <h3>Response</h3>
              <span className="status-pill">{statusText}</span>
              <div style={{marginLeft:12}}>
                <button className={`btn ${showFormatted ? 'primary' : 'ghost'}`} onClick={()=>setShowFormatted(true)}>Formatted</button>
                <button className={`btn ${!showFormatted ? 'primary' : 'ghost'}`} onClick={()=>setShowFormatted(false)}>JSON</button>
              </div>
            </div>
            {showFormatted ? (
              <div className="response-output formatted">
                {responseRaw ? (
                  <div dangerouslySetInnerHTML={{__html: renderFormattedResponse(responseRaw)}} />
                ) : (
                  <pre>{responseText || 'No output yet. Run a task request to see response.'}</pre>
                )}
              </div>
            ) : (
              <pre className="response-output">{responseRaw ? JSON.stringify(responseRaw, null, 2) : responseText || 'No output yet.'}</pre>
            )}
          </section>
        </main>
      </div>
    </div>
  )
}

export default AppPage

function renderFormattedResponse(payload){
  try{
    if(payload == null) return ''
    // Plain string
    if(typeof payload === 'string'){
      return `<p>${escapeHtml(payload)}</p>`
    }

    // Task A response format
    if(payload.predicted_rating !== undefined || payload.generated_review !== undefined){
      const rating = Number(payload.predicted_rating ?? payload.predictedRating ?? 0)
      const conf = payload.tone_confidence ?? payload.confidence ?? payload.toneConfidence
      const review = payload.generated_review ?? payload.generatedReview ?? payload.generated
      const basis = payload.behavioural_basis ?? payload.behaviouralBasis ?? payload.behavioural_basis
      return `
        <div>
          <p><strong>Predicted rating:</strong> <strong>${rating.toFixed(1)}</strong></p>
          <p><strong>Confidence:</strong> ${Number(conf ?? 0).toFixed(2)}</p>
          <p><strong>Review:</strong></p>
          <p>${escapeHtml(String(review || ''))}</p>
          <p><em>Basis:</em> ${escapeHtml(String(basis || ''))}</p>
        </div>
      `
    }

    // Recommendations response
    if(Array.isArray(payload.recommendations) || Array.isArray(payload.recommendations?.recommendations)){
      const recs = Array.isArray(payload.recommendations) ? payload.recommendations : payload.recommendations.recommendations
      let html = `<div><p><strong>Recommendations</strong></p>`
      for(const r of recs){
        const title = escapeHtml(r.item_name || r.itemName || r.item_name || r.item)
        const explanation = escapeHtml(r.explanation || r.reasoning || r.reason || '')
        const conf = Number(r.confidence ?? r.conf ?? 0).toFixed(2)
        html += `<div style="margin-bottom:12px"><p><strong style=\"font-size:1.05em\">${title}</strong> <span style=\"color:#666\">(confidence: ${conf})</span></p><p>${explanation}</p></div>`
      }
      html += `</div>`
      return html
    }

    // Fallback: pretty render JSON
    return `<pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`
  }catch(e){
    return `<pre>Unable to render response: ${escapeHtml(String(e))}</pre>`
  }
}

function escapeHtml(s){
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

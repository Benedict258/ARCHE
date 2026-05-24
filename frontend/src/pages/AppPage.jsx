import React, {useState} from 'react'
import TopNav from '../components/TopNav'
import Sidebar from '../components/Sidebar'

const AppPage = ()=>{
  const [res, setRes] = useState(null)
  const [userToken, setUserToken] = useState('demo_user_001')
  const [recommendationId, setRecommendationId] = useState('')

  async function fetchRecommend(){
    setRes({status: 'loading'})
    try{
      const r = await fetch('/v1/recommend', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({user_token: userToken, n:5, enable_live_data:false})
      })
      const j = await r.json()
      setRes(j)
    }catch(e){
      setRes({error: e.message})
    }
  }

  async function fetchSimulateReview(){
    setRes({status: 'loading'})
    try{
      const r = await fetch('/v1/simulate-review', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({user_token: userToken, review_history: [], context: {entry_point: 'web_demo'}})
      })
      const j = await r.json()
      setRes(j)
    }catch(e){
      setRes({error: e.message})
    }
  }

  async function fetchExplain(){
    if(!recommendationId){ setRes({error: 'Enter a recommendation id first'}); return }
    setRes({status: 'loading'})
    try{
      const r = await fetch('/v1/explain', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({user_token: userToken, recommendation_id: recommendationId})
      })
      const j = await r.json()
      setRes(j)
    }catch(e){
      setRes({error: e.message})
    }
  }

  return (
    <div style={{display:'flex',minHeight:'100vh'}}>
      <Sidebar />
      <div style={{flex:1}}>
        <TopNav />

        <div className="page small">
          <header className="hero small">
        <h2>ARCHE — Demo Console</h2>
        <p>Interact with the running API: simulate a review, request recommendations, or fetch explanation for a recommendation.</p>

        <div style={{display:'flex',gap:8,justifyContent:'center',marginTop:12}}>
          <input className="btn" value={userToken} onChange={e=>setUserToken(e.target.value)} style={{minWidth:220}} />
          <button className="btn primary" onClick={fetchRecommend}>Get Recommendations</button>
          <button className="btn" onClick={fetchSimulateReview}>Simulate Review</button>
        </div>

        <div style={{display:'flex',gap:8,justifyContent:'center',marginTop:10}}>
          <input className="btn" placeholder="recommendation_id" value={recommendationId} onChange={e=>setRecommendationId(e.target.value)} style={{minWidth:260}} />
          <button className="btn" onClick={fetchExplain}>Explain</button>
        </div>
      </header>

      <main className="content">
        {res ? (
          <div className="card-grid">
            <div className="card" style={{gridColumn:'1/-1'}}>
              <div style={{fontWeight:600,marginBottom:8}}>Response</div>
              <pre style={{whiteSpace:'pre-wrap',margin:0}}>{JSON.stringify(res, null, 2)}</pre>
            </div>
          </div>
        ) : (
          <p className="muted">No results yet — use the controls above.</p>
        )}
      </main>
      </div>
    </div>
  )
}

export default AppPage

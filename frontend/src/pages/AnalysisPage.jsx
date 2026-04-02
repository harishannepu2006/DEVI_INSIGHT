import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { repoAPI, analysisAPI, bugsAPI, insightsAPI } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function AnalysisPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [analysis, setAnalysis] = useState(null)
  const [repository, setRepository] = useState(null)
  const [bugs, setBugs] = useState([])
  const [insights, setInsights] = useState([])
  const [loading, setLoading] = useState(true)
  const [polling, setPolling] = useState(false)

  useEffect(() => {
    loadAnalysis()
  }, [id])

  async function loadAnalysis() {
    try {
      const { data } = await analysisAPI.get(id)
      setAnalysis(data)

      try {
        const repoRes = await repoAPI.get(data.repository_id)
        setRepository(repoRes.data)
      } catch(e) {}

      if (data.status === 'completed') {
        const [bugsRes, insightsRes] = await Promise.all([
          bugsAPI.byAnalysis(id),
          insightsAPI.byAnalysis(id)
        ])
        setBugs(bugsRes.data.bugs || [])
        setInsights(insightsRes.data.insights || [])
      } else if (data.status === 'queued' || data.status === 'running') {
        setPolling(true)
        setTimeout(() => loadAnalysis(), 5000)
      }
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>
  if (!analysis) return <div className="empty-state"><h3>Analysis not found</h3></div>

  if (analysis.status === 'queued' || analysis.status === 'running') {
    return (
      <div className="empty-state" style={{minHeight:'60vh'}}>
        <div className="spinner" style={{marginBottom:'24px'}} />
        <h3 className="empty-state-title">
          {analysis.status === 'queued' ? 'Analysis Queued' : 'Analysis Running'}
        </h3>
        <p className="empty-state-text">
          Your code is being analyzed. This usually takes 1-3 minutes.
        </p>
        <span className={`badge badge-status-${analysis.status}`} style={{marginTop:'16px'}}>
          {analysis.status}
        </span>
      </div>
    )
  }

  if (analysis.status === 'failed') {
    return (
      <div className="empty-state" style={{minHeight:'60vh'}}>
        <div className="empty-state-icon">❌</div>
        <h3 className="empty-state-title">Analysis Failed</h3>
        <p className="empty-state-text">{analysis.error_message || 'An error occurred during analysis.'}</p>
      </div>
    )
  }

  const fileMetrics = analysis.file_metrics || []
  const complexityChart = fileMetrics
    .sort((a, b) => b.complexity - a.complexity)
    .slice(0, 10)
    .map(f => ({ name: f.file_path.split('/').pop(), complexity: f.complexity, issues: f.issues_count }))

  const hotspots = analysis.hotspot_files || []

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analysis Results {repository ? `- ${repository.name}` : ''}</h1>
        <p className="page-description">{analysis.summary}</p>
        {repository && repository.description && (
          <p style={{marginTop:'8px', color:'var(--text-secondary)', fontSize:'14px', maxWidth:'800px'}}>
            📝 <strong>Description:</strong> {repository.description}
          </p>
        )}
      </div>

      {/* Metrics Overview */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{analysis.total_files}</div>
          <div className="stat-label">Files Analyzed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analysis.total_lines?.toLocaleString()}</div>
          <div className="stat-label">Lines of Code</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analysis.avg_complexity?.toFixed(1)}</div>
          <div className="stat-label">Avg Complexity</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{analysis.technical_debt_hours?.toFixed(1)}h</div>
          <div className="stat-label">Tech Debt</div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{fontSize:'24px', color:'var(--accent-emerald)'}}>
            {(100 - (analysis.risk_score || 0)).toFixed(0)}/100
          </div>
          <div className="stat-label">Health Score</div>
        </div>
      </div>

      {/* Action buttons */}
      <div style={{display:'flex', gap:'12px', marginBottom:'32px', flexWrap:'wrap'}}>
        <button className="btn btn-primary" onClick={() => navigate(`/bugs/${id}`)}>
          🐞 View Bugs ({bugs.length})
        </button>
        <button className="btn btn-secondary" onClick={() => navigate(`/history/${id}`)}>
          📜 View History
        </button>
        <button className="btn btn-secondary" onClick={() => navigate('/reports', {state:{analysisId:id}})}>
          📄 Generate Report
        </button>
      </div>

      <div className="charts-grid">
        {/* Complexity Chart */}
        {complexityChart.length > 0 && (
          <div className="chart-container">
            <div className="chart-title">Top 10 Complex Files</div>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={complexityChart} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" stroke="#64748b" fontSize={12} />
                <YAxis dataKey="name" type="category" width={120} stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{background:'#1e293b', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px'}} />
                <Bar dataKey="complexity" fill="#3b82f6" radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Hotspots */}
        {hotspots.length > 0 && (
          <div className="card">
            <div className="card-header">
              <div className="card-title">🔥 Hotspot Files</div>
            </div>
            <div style={{display:'flex', flexDirection:'column', gap:'8px'}}>
              {hotspots.slice(0, 10).map((h, i) => (
                <div key={i} style={{display:'flex', alignItems:'center', justifyContent:'space-between', padding:'10px 14px', background:'var(--bg-glass)', borderRadius:'8px'}}>
                  <span style={{fontSize:'13px', fontFamily:'monospace'}}>{h.file_path}</span>
                  <div style={{display:'flex', gap:'8px', alignItems:'center'}}>
                    <span style={{fontSize:'12px', color:'var(--text-muted)'}}>C: {h.complexity?.toFixed(1)}</span>
                    <span className={`badge badge-${h.risk_level}`}>{h.risk_level}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Bug Preview */}
      {bugs.length > 0 && (
        <div style={{marginTop:'32px'}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'16px'}}>
            <h3 style={{fontSize:'18px', fontWeight:'700'}}>🐞 Top Detected Bugs ({bugs.length} total)</h3>
            <button className="btn btn-primary" onClick={() => navigate(`/bugs/${id}`)}>
              View All Bugs & Chat
            </button>
          </div>
          <div style={{display:'flex', flexDirection:'column', gap:'12px'}}>
            {bugs.slice(0, 3).map(bug => (
              <div key={bug.id} className="card" style={{padding:'20px'}}>
                <div style={{display:'flex', justifyContent:'space-between', marginBottom:'12px'}}>
                  <div className="card-title">
                    <span className={`badge badge-${bug.severity}`} style={{marginRight:'8px'}}>{bug.severity}</span>
                    {bug.title}
                  </div>
                  <button className="btn btn-primary btn-sm" onClick={() => navigate(`/chat/${bug.id}`)}>
                    💬 Ask AI about this bug
                  </button>
                </div>
                <div style={{marginBottom:'12px', fontSize:'14px', color:'var(--text-secondary)'}}>
                  📁 {bug.file_path} (Line {bug.line_number || '?'})
                </div>
                
                {bug.buggy_code && (
                  <div style={{marginBottom:'12px'}}>
                    <span style={{fontSize:'12px', color:'var(--accent-rose)', fontWeight:'600'}}>Buggy Code:</span>
                    <div className="bug-code-block" style={{marginTop:'4px', padding:'12px', background:'rgba(0,0,0,0.3)', borderRadius:'8px', borderLeft:'4px solid var(--accent-rose)', fontFamily:'monospace', overflowX:'auto'}}>
                      <span className="code-diff-remove">{bug.buggy_code}</span>
                    </div>
                  </div>
                )}

                {bug.fixed_code && (
                  <div style={{marginBottom:'12px'}}>
                    <span style={{fontSize:'12px', color:'var(--accent-emerald)', fontWeight:'600'}}>Fix Recommendation:</span>
                    <div className="bug-code-block" style={{marginTop:'4px', padding:'12px', background:'rgba(0,0,0,0.3)', borderRadius:'8px', borderLeft:'4px solid var(--accent-emerald)', fontFamily:'monospace', overflowX:'auto'}}>
                      <span className="code-diff-add">{bug.fixed_code}</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights */}
      {insights.length > 0 && (
        <div style={{marginTop:'32px'}}>
          <h3 style={{fontSize:'18px', fontWeight:'700', marginBottom:'16px'}}>🤖 AI Insights</h3>
          <div style={{display:'flex', flexDirection:'column', gap:'12px'}}>
            {insights.map(insight => (
              <div key={insight.id} className={`insight-card severity-${insight.severity}`}>
                <div className="insight-header">
                  <div className="insight-title">{insight.title}</div>
                  <span className={`badge badge-${insight.severity}`}>{insight.severity}</span>
                </div>
                <div className="insight-description">{insight.description}</div>
                {insight.recommendation && (
                  <div className="insight-recommendation">💡 {insight.recommendation}</div>
                )}
                {insight.estimated_effort && (
                  <div style={{fontSize:'12px', color:'var(--text-muted)', marginTop:'8px'}}>
                    ⏱️ Estimated effort: {insight.estimated_effort}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

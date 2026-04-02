import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { analysisAPI } from '../services/api'

export default function HistoryPage() {
  const { analysisId } = useParams()
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadHistory()
  }, [analysisId])

  async function loadHistory() {
    try {
      const { data } = await analysisAPI.history(analysisId)
      setHistory(data.history || [])
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">📜 Analysis History</h1>
        <p className="page-description">Track how your code quality has changed over time</p>
      </div>

      {history.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📜</div>
          <h3 className="empty-state-title">No history yet</h3>
          <p className="empty-state-text">This repository only has one analysis. Run more to see trends.</p>
        </div>
      ) : (
        <div className="timeline">
          {history.map((item, i) => (
            <div key={item.id} className="timeline-item" onClick={() => navigate(`/analysis/${item.id}`)} style={{cursor:'pointer'}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:'12px'}}>
                <div>
                  <span style={{fontSize:'14px', fontWeight:'600'}}>Analysis #{history.length - i}</span>
                  <span style={{fontSize:'12px', color:'var(--text-muted)', marginLeft:'12px'}}>
                    {new Date(item.created_at).toLocaleString()}
                  </span>
                </div>
                <span className={`badge badge-${item.risk_level}`}>{item.risk_level}</span>
              </div>

              <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(120px, 1fr))', gap:'12px'}}>
                <div>
                  <div style={{fontSize:'18px', fontWeight:'700', color:'var(--accent-blue)'}}>{item.total_files}</div>
                  <div style={{fontSize:'11px', color:'var(--text-muted)'}}>Files</div>
                </div>
                <div>
                  <div style={{fontSize:'18px', fontWeight:'700', color:'var(--accent-cyan)'}}>{item.total_lines?.toLocaleString()}</div>
                  <div style={{fontSize:'11px', color:'var(--text-muted)'}}>Lines</div>
                </div>
                <div>
                  <div style={{fontSize:'18px', fontWeight:'700', color:'var(--accent-amber)'}}>{item.avg_complexity?.toFixed(1)}</div>
                  <div style={{fontSize:'11px', color:'var(--text-muted)'}}>Avg Complexity</div>
                </div>
                <div>
                  <div style={{fontSize:'18px', fontWeight:'700', color:'var(--accent-rose)'}}>{item.technical_debt_hours?.toFixed(1)}h</div>
                  <div style={{fontSize:'11px', color:'var(--text-muted)'}}>Tech Debt</div>
                </div>
                <div>
                  <div style={{fontSize:'18px', fontWeight:'700', color:'var(--accent-purple)'}}>{item.risk_score?.toFixed(0)}</div>
                  <div style={{fontSize:'11px', color:'var(--text-muted)'}}>Risk Score</div>
                </div>
              </div>

              {item.summary && (
                <p style={{marginTop:'12px', fontSize:'13px', color:'var(--text-secondary)'}}>{item.summary}</p>
              )}

              {/* Comparison with previous */}
              {i < history.length - 1 && (
                <div style={{marginTop:'12px', display:'flex', gap:'12px', fontSize:'12px'}}>
                  {(() => {
                    const prev = history[i + 1]
                    const complexDiff = item.avg_complexity - prev.avg_complexity
                    const riskDiff = item.risk_score - prev.risk_score
                    return (
                      <>
                        <span style={{color: complexDiff > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)'}}>
                          Complexity {complexDiff > 0 ? '↑' : '↓'} {Math.abs(complexDiff).toFixed(1)}
                        </span>
                        <span style={{color: riskDiff > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)'}}>
                          Risk {riskDiff > 0 ? '↑' : '↓'} {Math.abs(riskDiff).toFixed(0)}
                        </span>
                      </>
                    )
                  })()}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

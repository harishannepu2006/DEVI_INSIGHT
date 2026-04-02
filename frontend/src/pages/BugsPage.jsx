import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { bugsAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function BugsPage() {
  const { analysisId } = useParams()
  const navigate = useNavigate()
  const [bugs, setBugs] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    loadBugs()
  }, [analysisId, filter])

  async function loadBugs() {
    try {
      const [bugsRes, statsRes] = await Promise.all([
        bugsAPI.byAnalysis(analysisId, filter ? { severity: filter } : {}),
        bugsAPI.stats(analysisId)
      ])
      setBugs(bugsRes.data.bugs || [])
      setStats(statsRes.data)
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  async function handleResolve(bugId) {
    try {
      await bugsAPI.resolve(bugId)
      toast.success('Bug marked as resolved')
      setBugs(bugs.map(b => b.id === bugId ? {...b, is_resolved: true} : b))
    } catch (err) {
      toast.error('Failed to resolve bug')
    }
  }

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>

  const severities = ['critical', 'high', 'medium', 'low']

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">🐞 Bug Report</h1>
        <p className="page-description">{bugs.length} bugs found in this analysis</p>
      </div>

      {/* Bug Stats */}
      {stats && (
        <div className="stats-grid" style={{marginBottom:'24px'}}>
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Bugs</div>
          </div>
          {severities.map(sev => (
            <div key={sev} className="stat-card">
              <div className="stat-value" style={{fontSize:'24px'}}>
                <span className={`badge badge-${sev}`} style={{fontSize:'14px', padding:'4px 12px'}}>
                  {stats.by_severity?.[sev] || 0} {sev}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{display:'flex', gap:'8px', marginBottom:'24px', flexWrap:'wrap'}}>
        <button className={`btn btn-sm ${!filter ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('')}>
          All
        </button>
        {severities.map(sev => (
          <button key={sev} className={`btn btn-sm ${filter === sev ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter(sev)}>
            {sev.charAt(0).toUpperCase() + sev.slice(1)}
          </button>
        ))}
      </div>

      {/* Bug List */}
      {bugs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <h3 className="empty-state-title">No bugs found!</h3>
          <p className="empty-state-text">Great job — no issues detected for this filter.</p>
        </div>
      ) : (
        <div style={{display:'flex', flexDirection:'column', gap:'12px'}}>
          {bugs.map(bug => (
            <div key={bug.id} className="bug-card" style={{cursor: 'default'}}>
              <div className="bug-card-header">
                <div>
                  <span className={`badge badge-${bug.severity}`} style={{marginRight:'8px'}}>{bug.severity}</span>
                  <span className="bug-title">{bug.title}</span>
                </div>
                <div style={{display:'flex', gap:'8px'}}>
                  {bug.is_resolved && <span className="badge badge-low">resolved</span>}
                </div>
              </div>
              <div className="bug-meta">
                <span>📁 {bug.file_path}</span>
                <span>📍 Line {bug.line_number || '?'}</span>
                <span>🏷️ {bug.category || bug.bug_type}</span>
              </div>

              <div style={{marginTop:'16px'}}>
                  {bug.description && <p style={{fontSize:'14px', marginBottom:'12px', color:'var(--text-secondary)'}}>{bug.description}</p>}

                  {bug.buggy_code && (
                    <div style={{marginBottom:'8px'}}>
                      <span style={{fontSize:'12px', color:'var(--accent-rose)', fontWeight:'600'}}>Buggy Code:</span>
                      <div className="bug-code-block">
                        <span className="code-diff-remove">{bug.buggy_code}</span>
                      </div>
                    </div>
                  )}

                  {bug.fixed_code && (
                    <div style={{marginBottom:'8px'}}>
                      <span style={{fontSize:'12px', color:'var(--accent-emerald)', fontWeight:'600'}}>Fixed Code:</span>
                      <div className="bug-code-block">
                        <span className="code-diff-add">{bug.fixed_code}</span>
                      </div>
                    </div>
                  )}

                  {bug.explanation && (
                    <div style={{marginTop:'12px', padding:'12px', background:'var(--bg-glass)', borderRadius:'8px', fontSize:'13px', color:'var(--text-secondary)'}}>
                      💡 {bug.explanation}
                    </div>
                  )}

                  <div style={{display:'flex', gap:'8px', marginTop:'12px'}}>
                    <button className="btn btn-primary btn-sm" onClick={() => navigate(`/chat/${bug.id}`)}>
                      💬 Chat about this bug
                    </button>
                    {!bug.is_resolved && (
                      <button className="btn btn-secondary btn-sm" onClick={() => handleResolve(bug.id)}>
                        ✅ Mark Resolved
                      </button>
                    )}
                  </div>
                </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

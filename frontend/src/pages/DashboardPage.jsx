import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analysisAPI } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, 
         AreaChart, Area, ResponsiveContainer } from 'recharts'
import { HiOutlineFolder, HiOutlineSearch, HiOutlineExclamationCircle, 
         HiOutlineSparkles, HiOutlineExclamation } from 'react-icons/hi'

const COLORS = ['#f43f5e', '#f59e0b', '#06b6d4', '#10b981']

export default function DashboardPage() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    loadDashboard()
  }, [])

  async function loadDashboard() {
    try {
      const { data } = await analysisAPI.dashboard()
      setStats(data)
    } catch (err) {
      console.error('Dashboard error:', err)
    }
    setLoading(false)
  }

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>

  const riskData = stats ? Object.entries(stats.risk_distribution).map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value })) : []
  const langData = stats ? Object.entries(stats.language_distribution).map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), files: value })) : []
  const trendData = stats?.complexity_trend?.map((t, i) => ({
    index: i + 1,
    complexity: t.complexity,
    risk: t.risk_score,
    debt: t.debt_hours,
  })).reverse() || []

  const latestAnalysesByRepo = []
  const seenRepos = new Set()
  
  if (stats?.recent_analyses) {
      for (const a of stats.recent_analyses) {
          if (!seenRepos.has(a.repository_id)) {
              seenRepos.add(a.repository_id)
              latestAnalysesByRepo.push(a)
          }
      }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-description">Overview of your code quality intelligence</p>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card animate-in animate-delay-1">
          <span className="stat-icon"><HiOutlineFolder /></span>
          <div className="stat-value">{stats?.total_repos || 0}</div>
          <div className="stat-label">Repositories</div>
        </div>
        <div className="stat-card animate-in animate-delay-2">
          <span className="stat-icon"><HiOutlineSearch /></span>
          <div className="stat-value">{stats?.total_analyses || 0}</div>
          <div className="stat-label">Analyses</div>
        </div>
        <div className="stat-card animate-in animate-delay-3">
          <span className="stat-icon"><HiOutlineExclamationCircle /></span>
          <div className="stat-value">{stats?.total_bugs || 0}</div>
          <div className="stat-label">Bugs Found</div>
        </div>
        <div className="stat-card animate-in animate-delay-4">
          <span className="stat-icon"><HiOutlineSparkles /></span>
          <div className="stat-value">{stats?.total_insights || 0}</div>
          <div className="stat-label">AI Insights</div>
        </div>
        <div className="stat-card animate-in animate-delay-4">
          <span className="stat-icon"><HiOutlineSparkles style={{color:'var(--accent-emerald)'}} /></span>
          <div className="stat-value" style={{color:'var(--accent-emerald)'}}>
            {stats?.avg_risk_score !== undefined ? (100 - stats.avg_risk_score).toFixed(0) : 0}/100
          </div>
          <div className="stat-label">Overall Health Score</div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        <div className="chart-container animate-in">
          <div className="chart-title">Risk Distribution</div>
          {riskData.some(d => d.value > 0) ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={riskData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({name, value}) => value > 0 ? `${name}: ${value}` : ''}>
                  {riskData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{background:'#1e293b', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px'}} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{padding:'40px'}}>
              <p className="empty-state-text">No analysis data yet. Submit a repository to get started!</p>
            </div>
          )}
        </div>

        <div className="chart-container animate-in">
          <div className="chart-title">Languages</div>
          {langData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={langData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{background:'#1e293b', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px'}} />
                <Bar dataKey="files" fill="#3b82f6" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state" style={{padding:'40px'}}>
              <p className="empty-state-text">No language data available.</p>
            </div>
          )}
        </div>

        {trendData.length > 1 && (
          <div className="chart-container animate-in" style={{gridColumn:'1 / -1'}}>
            <div className="chart-title">Complexity Trend</div>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorComplexity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="index" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip contentStyle={{background:'#1e293b', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'8px'}} />
                <Area type="monotone" dataKey="complexity" stroke="#3b82f6" fillOpacity={1} fill="url(#colorComplexity)" />
                <Area type="monotone" dataKey="risk" stroke="#f43f5e" fillOpacity={0.1} fill="#f43f5e" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Repository Insights */}
      {latestAnalysesByRepo.length > 0 && (
        <div style={{marginTop:'32px'}}>
          <h2 style={{fontSize:'24px', fontWeight:'700', marginBottom:'16px'}}>Repository Overview</h2>
          <div style={{display:'flex', flexDirection:'column', gap:'24px'}}>
            {latestAnalysesByRepo.map(analysis => {
              const repoInsights = (stats?.recent_insights || []).filter(i => i.analysis_id === analysis.id);
              const repo = analysis.repositories;
              const healthScore = (100 - (analysis.risk_score || 0)).toFixed(0);
              const scoreColor = healthScore >= 75 ? 'var(--accent-emerald)' : healthScore >= 50 ? 'var(--accent-amber)' : 'var(--accent-rose)';
              
              return (
                <div key={analysis.id} className="card animate-in" style={{position:'relative', overflow:'hidden'}}>
                  <div style={{padding:'24px', borderBottom:'1px solid rgba(255,255,255,0.05)', display:'flex', justifyContent:'space-between', alignItems:'flex-start', flexWrap:'wrap', gap:'16px'}}>
                    <div style={{flex:'1 1 300px'}}>
                      <h2 style={{fontSize:'20px', fontWeight:'700', marginBottom:'8px'}}>
                        {repo?.name || 'Unknown Repository'}
                      </h2>
                      <p style={{color:'var(--text-secondary)', fontSize:'14px', lineHeight:'1.5'}}>
                        {repo?.description || 'No description provided.'}
                      </p>
                    </div>
                    
                    <div style={{textAlign:'right', minWidth:'120px'}}>
                      <div style={{fontSize:'12px', color:'var(--text-muted)', marginBottom:'4px', textTransform:'uppercase', letterSpacing:'1px', fontWeight:'600'}}>
                        Health Score
                      </div>
                      <div style={{fontSize:'36px', fontWeight:'800', color: scoreColor, lineHeight:'1'}}>
                        {healthScore}<span style={{fontSize:'16px', color:'var(--text-muted)', fontWeight:'400'}}>/100</span>
                      </div>
                    </div>
                  </div>

                  <div style={{padding:'24px'}}>
                    <h3 style={{fontSize:'14px', textTransform:'uppercase', letterSpacing:'1px', color:'var(--text-muted)', marginBottom:'16px', display:'flex', alignItems:'center', gap:'8px'}}>
                      <HiOutlineSparkles /> Top AI Insights
                    </h3>
                    
                    {repoInsights.length > 0 ? (
                      <div style={{display:'flex', flexDirection:'column', gap:'12px'}}>
                        {repoInsights.slice(0, 3).map(insight => (
                          <div key={insight.id} className="insight-card" style={{margin:0, borderLeft:`4px solid ${insight.severity === 'critical' || insight.severity === 'high' ? 'var(--accent-rose)' : 'var(--accent-amber)'}`}}>
                            <div className="insight-header">
                              <div className="insight-title" style={{fontSize:'14px'}}>{insight.title}</div>
                              <span className={`badge badge-${insight.severity}`} style={{transform:'scale(0.9)'}}>{insight.severity}</span>
                            </div>
                            <div className="insight-description" style={{marginTop:'6px', fontSize:'13px', color:'var(--text-secondary)'}}>{insight.description}</div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{fontSize:'13px', color:'var(--text-secondary)', fontStyle:'italic'}}>
                        No major AI insights detected for this repository's recent analysis.
                      </div>
                    )}
                    
                    <div style={{marginTop:'24px', display:'flex', gap:'12px'}}>
                      <button className="btn btn-primary btn-sm" onClick={() => navigate(`/analysis/${analysis.id}`)}>
                        Go to Details
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {!stats?.recent_analyses?.length && (
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <h3 className="empty-state-title">No analyses yet</h3>
          <p className="empty-state-text">Submit a GitHub repository or code snippet to get started with your first analysis.</p>
          <button className="btn btn-primary" style={{marginTop:'16px'}} onClick={() => navigate('/repositories')}>
            Submit Repository
          </button>
        </div>
      )}
    </div>
  )
}

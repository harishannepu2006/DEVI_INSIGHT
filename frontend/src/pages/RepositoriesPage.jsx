import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { repoAPI, analysisAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function RepositoriesPage() {
  const [repos, setRepos] = useState([])
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('url')
  const [repoUrl, setRepoUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [repoRes, analysisRes] = await Promise.all([repoAPI.list(), analysisAPI.list()])
      setRepos(repoRes.data.repositories || [])
      setAnalyses(analysisRes.data.analyses || [])
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  async function handleSubmitRepo(e) {
    e.preventDefault()
    if (!repoUrl.trim()) return toast.error('Enter a repository URL')
    setSubmitting(true)
    try {
      const { data } = await repoAPI.submit(repoUrl.trim(), branch)
      toast.success('Repository submitted for analysis!')
      setRepoUrl('')
      navigate(`/analysis/${data.analysis_id}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit repository')
    }
    setSubmitting(false)
  }

  async function handleSubmitSnippet(e) {
    e.preventDefault()
    if (!code.trim()) return toast.error('Enter some code')
    setSubmitting(true)
    try {
      const { data } = await repoAPI.submitSnippet(code, language, `snippet.${language === 'python' ? 'py' : 'js'}`)
      toast.success('Snippet submitted for analysis!')
      setCode('')
      navigate(`/analysis/${data.analysis_id}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to analyze snippet')
    }
    setSubmitting(false)
  }

  async function handleDelete(id) {
    if (!confirm('Delete this repository?')) return
    try {
      await repoAPI.delete(id)
      toast.success('Repository deleted')
      setRepos(repos.filter(r => r.id !== id))
    } catch (err) {
      toast.error('Failed to delete')
    }
  }

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Repositories</h1>
        <p className="page-description">Submit a repository or code snippet for analysis</p>
      </div>

      <div className="submit-section">
        <div className="submit-card">
          <div className="tab-buttons">
            <button className={`tab-btn ${tab === 'url' ? 'active' : ''}`} onClick={() => setTab('url')}>
              GitHub URL
            </button>
            <button className={`tab-btn ${tab === 'snippet' ? 'active' : ''}`} onClick={() => setTab('snippet')}>
              Code Snippet
            </button>
          </div>

          {tab === 'url' ? (
            <form onSubmit={handleSubmitRepo}>
              <div className="form-group">
                <label className="form-label">Repository URL</label>
                <input
                  className="form-input"
                  placeholder="https://github.com/user/repo"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Branch</label>
                <input
                  className="form-input"
                  placeholder="main"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                />
              </div>
              <button className="btn btn-primary" disabled={submitting}>
                {submitting ? '⏳ Analyzing...' : '🔍 Analyze Repository'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleSubmitSnippet}>
              <div className="form-group">
                <label className="form-label">Language</label>
                <select className="form-input" value={language} onChange={(e) => setLanguage(e.target.value)} style={{cursor:'pointer'}}>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="typescript">TypeScript</option>
                  <option value="java">Java</option>
                  <option value="c">C</option>
                  <option value="cpp">C++</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Code</label>
                <textarea
                  className="form-textarea"
                  placeholder="Paste your code here..."
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  rows={10}
                  style={{fontFamily:'monospace'}}
                />
              </div>
              <button className="btn btn-primary" disabled={submitting}>
                {submitting ? '⏳ Analyzing...' : '🔍 Analyze Snippet'}
              </button>
            </form>
          )}
        </div>
      </div>

      {/* Repository List */}
      {repos.length > 0 && (
        <div style={{marginTop:'32px'}}>
          <h3 style={{fontSize:'18px', fontWeight:'700', marginBottom:'16px'}}>Your Repositories</h3>
          <div className="repo-list">
            {repos.map(repo => {
              const latestAnalysis = analyses.find(a => a.repository_id === repo.id)
              return (
                <div key={repo.id} className="repo-card" onClick={() => latestAnalysis && navigate(`/analysis/${latestAnalysis.id}`)}>
                  <div className="repo-info">
                    <div className="repo-name">{repo.name}</div>
                    <div className="repo-url">{repo.url || 'Code snippet'}</div>
                    {repo.language && <span className="badge badge-medium" style={{marginTop:'8px'}}>{repo.language}</span>}
                  </div>
                  <div className="repo-actions" onClick={e => e.stopPropagation()} style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                    {latestAnalysis && latestAnalysis.status === 'completed' && (
                      <button 
                        className="btn btn-primary btn-sm" 
                        onClick={(e) => { e.stopPropagation(); navigate(`/repo/${repo.id}/insights`); }}
                      >
                        ✨ View AI Insights
                      </button>
                    )}
                    {latestAnalysis && (
                      <span className={`badge badge-status-${latestAnalysis.status}`}>{latestAnalysis.status}</span>
                    )}
                    <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(repo.id)}>🗑️</button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

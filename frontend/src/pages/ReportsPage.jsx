import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { reportsAPI, analysisAPI } from '../services/api'
import toast from 'react-hot-toast'

export default function ReportsPage() {
  const location = useLocation()
  const [analyses, setAnalyses] = useState([])
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [selectedAnalysis, setSelectedAnalysis] = useState(location.state?.analysisId || '')
  const [reportType, setReportType] = useState('full')
  const [format, setFormat] = useState('pdf')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [analysesRes, reportsRes] = await Promise.all([
        analysisAPI.list(),
        reportsAPI.list()
      ])
      setAnalyses((analysesRes.data.analyses || []).filter(a => a.status === 'completed'))
      setReports(reportsRes.data.reports || [])
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  async function handleGenerate() {
    if (!selectedAnalysis) return toast.error('Select an analysis')
    setGenerating(true)
    try {
      const response = await reportsAPI.generate(selectedAnalysis, reportType, format)
      const reportId = response.data.report_id
      const filename = `devinsight_report_${reportType}.${format}`
      
      const token = localStorage.getItem('access_token')
      window.location.href = `${reportsAPI.downloadUrl(reportId, filename)}?token=${token}`

      toast.success('Report generation started!')
      setTimeout(loadData, 2000) // Refresh list after delay
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate report')
    }
    setGenerating(false)
  }

  async function handleDownload(reportId, rType, rFormat) {
    try {
      const filename = `devinsight_report_${rType}.${rFormat}`
      const token = localStorage.getItem('access_token')
      window.location.href = `${reportsAPI.downloadUrl(reportId, filename)}?token=${token}`
      toast.success('Download starting...')
    } catch (err) {
      toast.error('Download failed')
    }
  }

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">📄 Reports</h1>
        <p className="page-description">Generate and download comprehensive code quality reports</p>
      </div>

      <div className="submit-card" style={{maxWidth:'600px'}}>
        <h3>Generate New Report</h3>

        <div className="form-group">
          <label className="form-label">Analysis</label>
          <select className="form-input" value={selectedAnalysis} onChange={(e) => setSelectedAnalysis(e.target.value)} style={{cursor:'pointer'}}>
            <option value="">Select an analysis...</option>
            {analyses.map(a => (
              <option key={a.id} value={a.id}>
                {new Date(a.created_at).toLocaleDateString()} — {a.repositories?.name || 'Unknown Repo'} ({a.total_files} files)
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Report Type</label>
          <div className="tab-buttons">
            {[
              {value: 'full', label: '📊 Full'},
              {value: 'bugs_only', label: '🐞 Bugs'},
              {value: 'insights_only', label: '🤖 Insights'},
            ].map(t => (
              <button key={t.value} className={`tab-btn ${reportType === t.value ? 'active' : ''}`} onClick={() => setReportType(t.value)}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Format</label>
          <div className="tab-buttons">
            {[
              {value: 'pdf', label: '📕 PDF'},
              {value: 'docx', label: '📘 DOCX'},
              {value: 'json', label: '📗 JSON'},
            ].map(f => (
              <button key={f.value} className={`tab-btn ${format === f.value ? 'active' : ''}`} onClick={() => setFormat(f.value)}>
                {f.label}
              </button>
            ))}
          </div>
        </div>

        <button className="btn btn-primary btn-lg" style={{width:'100%'}} onClick={handleGenerate} disabled={generating || !selectedAnalysis}>
          {generating ? '⏳ Generating...' : '📥 Generate & Download'}
        </button>
      </div>

      {/* Past Reports */}
      {reports.length > 0 && (
        <div style={{marginTop:'32px'}}>
          <h3 style={{fontSize:'18px', fontWeight:'700', marginBottom:'16px'}}>Report History</h3>
          <div className="card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Format</th>
                  <th>Generated</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {reports.map(r => (
                  <tr key={r.id}>
                    <td><span className="badge badge-medium">{r.report_type?.replace('_', ' ')}</span></td>
                    <td>{r.format?.toUpperCase()}</td>
                    <td style={{color:'var(--text-muted)'}}>{new Date(r.generated_at || r.created_at).toLocaleString()}</td>
                    <td>
                      <button 
                        className="btn btn-ghost btn-sm" 
                        onClick={() => handleDownload(r.id, r.report_type, r.format)}
                        title="Download Report"
                      >
                        📥 Download
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

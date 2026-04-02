import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { repoAPI } from '../services/api';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Legend
} from 'recharts';
import { motion } from 'framer-motion';
import html2pdf from 'html2pdf.js';
import toast from 'react-hot-toast';
import { 
  HiOutlineDocumentDownload, HiOutlineChevronLeft, HiOutlineLibrary,
  HiOutlineShieldCheck, HiOutlineExclamationCircle 
} from 'react-icons/hi';

export default function InsightsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInsights() {
      try {
        const res = await repoAPI.getInsights(id);
        setData(res.data);
      } catch (err) {
        toast.error('Failed to load insights. Does this repo have a completed analysis?');
      } finally {
        setLoading(false);
      }
    }
    fetchInsights();
  }, [id]);

  const downloadPDF = () => {
    const element = document.getElementById('insights-dashboard');
    const opt = {
      margin: 10,
      filename: `DevInsight-Report-${id}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    toast.success('Generating PDF...');
    html2pdf().set(opt).from(element).save();
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="page-header skeleton" style={{ width: '300px', height: '40px', marginBottom: '20px', borderRadius: '8px' }}></div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div className="skeleton card" style={{ height: '200px' }}></div>
          <div className="skeleton card" style={{ height: '200px' }}></div>
          <div className="skeleton card" style={{ height: '400px', gridColumn: '1 / -1' }}></div>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <h2>No Insights Available</h2>
        <p style={{ color: 'var(--text-secondary)' }}>You need to run a successful analysis first.</p>
        <button className="btn btn-primary" onClick={() => navigate('/repositories')} style={{ marginTop: '16px' }}>
          Back to Repositories
        </button>
      </div>
    );
  }

  const { metrics, ai_summary, recommendations, charts, health_score, risk_level } = data;

  // Chart colors derived from CSS variables mapping
  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#f43f5e', '#8b5cf6', '#06b6d4'];
  const riskColors = {
    critical: '#f43f5e',
    high: '#f59e0b',
    medium: '#06b6d4',
    low: '#10b981'
  };

  // Prepare hotspot data
  const hotspotData = (charts.risk_distribution || []).map(h => ({
    name: h.file_path.split('/').pop(),
    complexity: h.complexity
  })).slice(0, 10);

  // Prepare language data for Donut Chart
  const langEntries = Object.entries(charts.language_distribution || {});
  const langData = langEntries.map(([name, val]) => ({
    name, value: val
  }));

  // Format complexity trend
  const trendData = (charts.complexity_trend || []).map((t, idx) => ({
    name: `Analysis \${idx + 1}`,
    complexity: t.complexity
  }));

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 100 } }
  };

  return (
    <div className="insights-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <button className="btn btn-ghost btn-icon" onClick={() => navigate('/repositories')}>
            <HiOutlineChevronLeft size={24} />
          </button>
          <div>
            <h1 className="page-title" style={{ marginBottom: 0 }}>AI Insights Dashboard</h1>
            <p className="page-description">Deep architectural overview for your repository</p>
          </div>
        </div>
        <button className="btn btn-secondary" onClick={downloadPDF}>
          <HiOutlineDocumentDownload size={20} />
          Download PDF
        </button>
      </div>

      <motion.div 
        id="insights-dashboard"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* A. Overview Section */}
        <motion.div variants={itemVariants} className="card" style={{ marginBottom: '24px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h2 style={{ fontSize: '24px', fontWeight: '800', marginBottom: '8px' }}>Repository Overview</h2>
              <div style={{ display: 'flex', gap: '16px', color: 'var(--text-secondary)', fontSize: '14px' }}>
                <span><HiOutlineLibrary style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }}/>{Object.keys(charts.language_distribution || {}).join(', ')}</span>
                <span>Last Updated: {new Date(data.created_at).toLocaleDateString()}</span>
              </div>
            </div>
            
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Health Score</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '150px', height: '8px', background: 'var(--bg-glass)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{ 
                    height: '100%', 
                    width: `\${health_score}%`, 
                    background: riskColors[risk_level] || 'var(--accent-blue)',
                    transition: 'width 1s ease-in-out'
                  }} />
                </div>
                <span style={{ fontSize: '32px', fontWeight: '800', color: riskColors[risk_level] }}>
                  {health_score.toFixed(1)}
                </span>
              </div>
              <span className={`badge badge-\${risk_level}`} style={{ marginTop: '8px', fontSize: '12px' }}>
                {risk_level.toUpperCase()} RISK
              </span>
            </div>
          </div>
        </motion.div>

        {/* C. AI Insights (Main Feature) */}
        <motion.div variants={itemVariants} className="card" style={{ marginBottom: '24px', background: 'var(--gradient-card)' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '24px' }}>🤖</span> AI Technical Breakdown
          </h3>
          <p style={{ fontSize: '16px', lineHeight: '1.7', color: 'var(--text-primary)' }}>
            {ai_summary}
          </p>
        </motion.div>

        {/* Breakdown Metrics */}
        <motion.div variants={itemVariants} className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Cyclomatic Complexity</div>
            <div className="stat-value">{metrics.avg_complexity?.toFixed(2)}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Avg per file</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Code Smells</div>
            <div className="stat-value">{metrics.total_issues}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Total flagged issues</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Tech Debt</div>
            <div className="stat-value">{metrics.technical_debt_hours?.toFixed(1)}h</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Estimated removal effort</div>
          </div>
        </motion.div>
        
        <motion.div variants={itemVariants} className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Bug Density</div>
            <div className="stat-value">{metrics.bug_density}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Per 1000 LOC</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Maintainability</div>
            <div className="stat-value">{metrics.maintainability_index?.toFixed(0)}/100</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Index Score</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Duplication</div>
            <div className="stat-value">{metrics.duplication_percentage}%</div>
            <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>Percentage of codebase</div>
          </div>
        </motion.div>

        {/* B. Visual Analytics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '24px', marginBottom: '24px' }}>
          
          <motion.div variants={itemVariants} className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Top Hotspot Files (Complexity)</h3>
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hotspotData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis type="number" stroke="var(--text-secondary)" />
                  <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 11 }} stroke="var(--text-secondary)" />
                  <Tooltip cursor={{ fill: 'var(--bg-glass)' }} contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
                  <Bar dataKey="complexity" fill="var(--accent-purple)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

          {trendData.length > 0 && (
            <motion.div variants={itemVariants} className="card">
              <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Complexity Trend</h3>
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                    <XAxis dataKey="name" stroke="var(--text-secondary)" />
                    <YAxis stroke="var(--text-secondary)" />
                    <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
                    <Line type="monotone" dataKey="complexity" stroke="var(--accent-blue)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </motion.div>
          )}

          <motion.div variants={itemVariants} className="card">
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px' }}>Language Distribution</h3>
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={langData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                    {langData.map((entry, index) => (
                      <Cell key={`cell-\${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '8px' }} />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </motion.div>

        </div>

        {/* E. Recommendations Section */}
        <motion.div variants={itemVariants} className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <HiOutlineShieldCheck style={{ color: 'var(--accent-emerald)', fontSize: '24px' }} /> Key Recommendations
          </h3>
          <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {recommendations.map((rec, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', background: 'var(--bg-glass)', borderRadius: '8px' }}>
                <HiOutlineExclamationCircle style={{ color: 'var(--accent-amber)', fontSize: '20px', flexShrink: 0, marginTop: '2px' }} />
                <span style={{ fontSize: '14px', lineHeight: '1.5' }}>{rec}</span>
              </li>
            ))}
          </ul>
        </motion.div>

      </motion.div>
      
      <style>{`
        .skeleton {
          animation: pulse 1.5s infinite ease-in-out;
          background: linear-gradient(90deg, var(--bg-card) 0%, var(--bg-hover) 50%, var(--bg-card) 100%);
          background-size: 200% 100%;
        }
        @keyframes pulse {
          0% { background-position: 100% 0; }
          100% { background-position: -100% 0; }
        }
      `}</style>
    </div>
  );
}

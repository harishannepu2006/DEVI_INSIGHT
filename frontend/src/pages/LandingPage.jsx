import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { HiOutlineCode, HiOutlineLightningBolt, HiOutlineShieldCheck, 
         HiOutlineChartBar, HiOutlineDocumentText, HiOutlineChatAlt2 } from 'react-icons/hi'

export default function LandingPage() {
  const navigate = useNavigate()
  const { user } = useAuth()

  const features = [
    { icon: <HiOutlineCode />, title: 'Code Analysis', desc: 'Deep static analysis with cyclomatic complexity, technical debt estimation, and risk classification.', color: '#3b82f6' },
    { icon: <HiOutlineLightningBolt />, title: 'Bug Detection', desc: 'AST-based bug detection with automatic fix generation for Python and JavaScript.', color: '#f59e0b' },
    { icon: <HiOutlineShieldCheck />, title: 'Security Scanning', desc: 'Detect SQL injection, XSS, hardcoded secrets, and command injection vulnerabilities.', color: '#f43f5e' },
    { icon: <HiOutlineChartBar />, title: 'Visual Dashboards', desc: 'Interactive charts showing complexity trends, risk distribution, and hotspot heatmaps.', color: '#10b981' },
    { icon: <HiOutlineChatAlt2 />, title: 'AI Bug Chatbot', desc: 'Each bug gets its own AI chatbot that explains issues and suggests improvements.', color: '#8b5cf6' },
    { icon: <HiOutlineDocumentText />, title: 'Reports', desc: 'Download comprehensive reports in PDF, DOCX, or JSON format with full metrics.', color: '#06b6d4' },
  ]

  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <div className="landing-logo">
          🔷 <span>DevInsight</span>
        </div>
        <div style={{display:'flex', gap:'12px'}}>
          {user ? (
            <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </button>
          ) : (
            <button className="btn btn-primary" onClick={() => navigate('/login')}>
              Get Started
            </button>
          )}
        </div>
      </nav>

      <section className="hero-section">
        <div className="hero-badge">⚡ AI-Powered Code Intelligence</div>
        <h1 className="hero-title">
          Ship Better Code<br />
          <span className="gradient-text">with AI Insights</span>
        </h1>
        <p className="hero-subtitle">
          DevInsight analyzes your repositories for bugs, technical debt, code smells, 
          and security vulnerabilities — then provides actionable AI-powered fixes.
        </p>
        <div className="hero-cta">
          <button className="btn btn-primary btn-lg" onClick={() => navigate(user ? '/dashboard' : '/login')}>
            Start Analyzing →
          </button>
          <button className="btn btn-secondary btn-lg" onClick={() => document.querySelector('.features-section')?.scrollIntoView({behavior:'smooth'})}>
            Learn More
          </button>
        </div>
      </section>

      <section className="features-section">
        <h2>Everything You Need</h2>
        <p className="section-subtitle">Comprehensive code quality intelligence in one platform.</p>
        <div className="features-grid">
          {features.map((f, i) => (
            <div key={i} className="feature-card animate-in animate-delay-1" style={{animationDelay: `${i * 0.1}s`}}>
              <div className="feature-icon" style={{background: `${f.color}20`, color: f.color}}>
                {f.icon}
              </div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer style={{textAlign:'center', padding:'40px', color:'var(--text-muted)', fontSize:'13px', borderTop:'1px solid var(--border-color)'}}>
        © 2026 DevInsight — Code Quality Intelligence Platform
      </footer>
    </div>
  )
}

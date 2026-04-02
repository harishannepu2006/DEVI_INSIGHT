import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { 
  HiOutlineViewGrid, HiOutlineFolder, HiOutlineDocumentReport,
  HiOutlineLogout, HiOutlineClock
} from 'react-icons/hi'
import ThemeToggle from './ThemeToggle'

export default function AppLayout({ children }) {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: <HiOutlineViewGrid /> },
    { path: '/repositories', label: 'Repositories', icon: <HiOutlineFolder /> },
    { path: '/reports', label: 'Reports', icon: <HiOutlineDocumentReport /> },
  ]

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo" onClick={() => navigate('/dashboard')} style={{cursor:'pointer'}}>
          <div className="logo-icon">D</div>
          <h1>DevInsight</h1>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <ThemeToggle />

        <div className="sidebar-footer">
          {user && (
            <div className="user-info">
              <div className="user-avatar">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={user.full_name} />
                ) : (
                  user.full_name?.charAt(0) || user.email?.charAt(0) || '?'
                )}
              </div>
              <div className="user-details">
                <div className="user-name">{user.full_name || 'User'}</div>
                <div className="user-email">{user.email}</div>
              </div>
            </div>
          )}
          <button className="nav-link" onClick={handleSignOut} style={{marginTop: '8px'}}>
            <span className="nav-icon"><HiOutlineLogout /></span>
            Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

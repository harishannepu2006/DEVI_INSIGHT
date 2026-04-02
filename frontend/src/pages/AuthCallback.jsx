import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../services/supabase'

export default function AuthCallback() {
  const navigate = useNavigate()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        if (error) throw error

        if (session) {
          localStorage.setItem('access_token', session.access_token)
          localStorage.setItem('refresh_token', session.refresh_token)
          navigate('/dashboard', { replace: true })
        } else {
          navigate('/login', { replace: true })
        }
      } catch (err) {
        console.error('Auth callback error:', err)
        navigate('/login', { replace: true })
      }
    }

    // Wait a moment for Supabase to process the auth hash
    setTimeout(handleCallback, 500)
  }, [navigate])

  return (
    <div className="loading-spinner" style={{minHeight:'100vh'}}>
      <div style={{textAlign:'center'}}>
        <div className="spinner" style={{margin:'0 auto 16px'}} />
        <p style={{color:'var(--text-secondary)'}}>Completing sign in...</p>
      </div>
    </div>
  )
}

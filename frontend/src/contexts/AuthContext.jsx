import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../services/supabase'
import { authAPI } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    checkSession()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          localStorage.setItem('access_token', session.access_token)
          localStorage.setItem('refresh_token', session.refresh_token)

          const userData = {
            id: session.user.id,
            email: session.user.email,
            full_name: session.user.user_metadata?.full_name || '',
            avatar_url: session.user.user_metadata?.avatar_url || '',
          }
          setUser(userData)
          localStorage.setItem('user', JSON.stringify(userData))

          // Sync with backend
          try {
            await authAPI.callback({
              access_token: session.access_token,
              refresh_token: session.refresh_token,
            })
          } catch (err) {
            console.error('Backend sync error:', err)
          }
        } else if (event === 'SIGNED_OUT') {
          setUser(null)
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
        }
        setLoading(false)
      }
    )

    return () => subscription?.unsubscribe()
  }, [])

  async function checkSession() {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        localStorage.setItem('access_token', session.access_token)
        const userData = {
          id: session.user.id,
          email: session.user.email,
          full_name: session.user.user_metadata?.full_name || '',
          avatar_url: session.user.user_metadata?.avatar_url || '',
        }
        setUser(userData)
        localStorage.setItem('user', JSON.stringify(userData))
      } else {
        // Check local storage
        const stored = localStorage.getItem('user')
        if (stored) setUser(JSON.parse(stored))
      }
    } catch (err) {
      console.error('Session check error:', err)
    }
    setLoading(false)
  }

  async function signInWithEmail(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
    return data
  }

  async function signUpWithEmail(email, password, fullName = '') {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName }
      }
    })
    if (error) throw error
    return data
  }

  async function signInWithGoogle() {
    const redirectUrl = window.location.hostname === 'localhost' 
      ? `${window.location.origin}/auth/callback` 
      : 'https://deviinsight.vercel.app/auth/callback';

    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: redirectUrl,
      },
    })
    if (error) throw error
  }

  async function signOut() {
    await supabase.auth.signOut()
    setUser(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, signInWithEmail, signUpWithEmail, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}

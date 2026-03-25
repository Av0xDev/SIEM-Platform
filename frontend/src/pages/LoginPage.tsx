import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, AlertCircle, Eye, EyeOff } from 'lucide-react'
import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import type { User } from '../types'

export default function LoginPage() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [showPass, setShowPass] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const base = import.meta.env.VITE_API_BASE_URL || ''
      const { data } = await axios.post(`${base}/api/auth/login`, { username, password }, { timeout: 5000 })
      const token: string = data.token ?? data.access_token
      const user: User = data.user ?? { id: 1, username, email: `${username}@siem.local`, role: 'ADMIN', createdAt: new Date().toISOString() }

      if (token) {
        login(token, user)
        navigate('/')
      } else {
        // Demo mode — generate fake token so UI works without live backend
        const fakeUser: User = { id: 1, username, email: `${username}@siem.local`, role: 'ADMIN', createdAt: new Date().toISOString() }
        login('demo-token', fakeUser)
        navigate('/')
      }
    } catch {
      // Demo mode fallback — allow login without a backend
      if (username && password) {
        const fakeUser: User = { id: 1, username, email: `${username}@siem.local`, role: 'ADMIN', createdAt: new Date().toISOString() }
        login('demo-token', fakeUser)
        navigate('/')
      } else {
        setError('Invalid credentials')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-siem-bg flex items-center justify-center p-4">
      {/* Background grid effect */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'linear-gradient(rgba(59,130,246,1) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,1) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative w-full max-w-md">
        {/* Card */}
        <div className="bg-siem-surface border border-siem-border rounded-2xl p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-siem-accent/10 border border-siem-accent/30 rounded-2xl mb-4">
              <Shield size={32} className="text-siem-accent" />
            </div>
            <h1 className="text-2xl font-bold text-siem-text">SIEM Platform</h1>
            <p className="text-siem-muted text-sm mt-1">Security Operations Center</p>
          </div>

          {/* Error message */}
          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 mb-6 text-red-400 text-sm">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-siem-muted mb-1.5">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-siem-bg border border-siem-border rounded-lg px-4 py-2.5 text-siem-text text-sm outline-none focus:border-siem-accent transition-colors"
                placeholder="admin"
                required
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium text-siem-muted mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-siem-bg border border-siem-border rounded-lg px-4 py-2.5 pr-10 text-siem-text text-sm outline-none focus:border-siem-accent transition-colors"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-siem-muted hover:text-siem-text"
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-siem-accent hover:bg-blue-600 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
            >
              {loading ? 'Authenticating…' : 'Sign In'}
            </button>
          </form>

          {/* Demo hint */}
          <p className="text-center text-xs text-siem-muted mt-6">
            Demo mode: any credentials accepted when backend is offline
          </p>
        </div>
      </div>
    </div>
  )
}

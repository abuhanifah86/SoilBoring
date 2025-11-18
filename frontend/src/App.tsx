import { useEffect, useState } from 'react'
import DailyReportForm from './tabs/DailyReportForm'
import QA from './tabs/QA'
import Summary from './tabs/Summary'
import Dashboard from './tabs/Dashboard'
import DailyReportData from './tabs/DailyReportData'
import AboutSoilBoring from './tabs/AboutSoilBoring'
import UserAdmin from './tabs/UserAdmin'
import Login from './Login'
import { login as loginApi, setAuthToken, setUnauthorizedHandler } from './api'

type TabKey = 'report' | 'qa' | 'summary' | 'dashboard' | 'reportData' | 'about' | 'users'
type AuthState = { token: string; email: string; role: 'admin' | 'general' } | null
const AUTH_STORAGE_KEY = 'ddr-auth'

export default function App() {
  const [tab, setTab] = useState<TabKey>('report')
  const [auth, setAuth] = useState<AuthState>(() => {
    if (typeof window === 'undefined') return null
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY)
    if (!raw) return null
    try {
      const parsed = JSON.parse(raw)
      if (parsed?.token && parsed?.email) {
        const role = parsed?.role === 'general' ? 'general' : 'admin'
        return { token: parsed.token, email: parsed.email, role }
      }
    } catch {
      return null
    }
    return null
  })
  const [authNotice, setAuthNotice] = useState('')

  useEffect(() => {
    setAuthToken(auth?.token ?? null)
    if (typeof window === 'undefined') return
    if (auth) {
      window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth))
    } else {
      window.localStorage.removeItem(AUTH_STORAGE_KEY)
    }
  }, [auth])

  useEffect(() => {
    const handler = () => {
      setAuth(null)
      setAuthNotice('Your session has expired. Please sign in again.')
    }
    setUnauthorizedHandler(handler)
    return () => setUnauthorizedHandler(null)
  }, [])

  const handleLogin = async (email: string, password: string) => {
    const session = await loginApi(email, password)
    setAuth({ token: session.token, email: session.email, role: session.role })
    setAuthNotice('')
    setTab('report')
  }

  const handleLogout = () => {
    setAuth(null)
    setAuthNotice('')
    setAuthToken(null)
  }

  const isAdmin = auth?.role === 'admin'
  useEffect(() => {
    if (tab === 'users' && !isAdmin) {
      setTab('report')
    }
  }, [tab, isAdmin])

  const tabs: { key: TabKey, label: string }[] = [
    { key: 'report', label: 'Borehole Log' },
    { key: 'qa', label: 'Geo AI' },
    { key: 'summary', label: 'Summaries' },
    { key: 'dashboard', label: 'Dashboard' },
    { key: 'reportData', label: 'Borehole Data' },
    { key: 'about', label: 'About' },
    ...(isAdmin ? [{ key: 'users' as const, label: 'Users' }] : []),
  ]

  if (!auth) {
    return (
      <div>
        {authNotice && (
          <div className="card" style={{ maxWidth: '480px', margin: '2rem auto', padding: '1rem', color: 'var(--danger, #c62828)' }}>
            {authNotice}
          </div>
        )}
        <Login onLogin={handleLogin} />
      </div>
    )
  }

  return (
    <div>
      <div className="actions" style={{ justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '.5rem' }}>
        <span>Signed in as <strong>{auth.email}</strong> ({auth.role})</span>
        <button onClick={handleLogout}>Sign Out</button>
      </div>
      <nav>
        {tabs.map(t => (
          <button
            key={t.key}
            className={tab === t.key ? 'active' : ''}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <div className="container">
        {tab === 'report' && <DailyReportForm />}
        {tab === 'qa' && <QA />}
        {tab === 'summary' && <Summary />}
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'reportData' && <DailyReportData />}
        {tab === 'about' && <AboutSoilBoring />}
        {tab === 'users' && isAdmin && <UserAdmin currentUserEmail={auth.email} />}
      </div>
    </div>
  )
}

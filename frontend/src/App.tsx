import { useState, useEffect } from 'react'
import './App.css'

interface HealthResponse {
  status: string
  service: string
  version: string
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setHealth(data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div className="app loading">Loading...</div>
  }

  if (error) {
    return (
      <div className="app error">
        <h1>Error</h1>
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div className="app">
      <header>
        <h1>atlas-forge-145-alan-vo</h1>
        <p>Write HTML. Render video. Built for agents.</p>
      </header>
      <main>
        <section className="health-card">
          <h2>Service Health</h2>
          {health && (
            <dl>
              <dt>Status</dt>
              <dd className={health.status === 'ok' ? 'ok' : 'error'}>{health.status}</dd>
              <dt>Service</dt>
              <dd>{health.service}</dd>
              <dt>Version</dt>
              <dd>{health.version}</dd>
            </dl>
          )}
        </section>
        <section className="features">
          <h2>Features</h2>
          <ul>
            <li>Bounded media range responses (fixes connection starvation)</li>
            <li>OIDC authentication with Keycloak</li>
            <li>LLM provider adapters</li>
            <li>Video composition & rendering</li>
          </ul>
        </section>
      </main>
      <footer>
        <p>Alan Vo &lt;alanvo@gmail.com&gt; | AI & Machine Learning</p>
      </footer>
    </div>
  )
}

export default App

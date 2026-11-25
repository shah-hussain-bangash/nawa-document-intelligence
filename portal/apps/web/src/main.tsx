import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './styles.css'
import './uae-theme.css'

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    return this.state.failed ? (
      <div className="fatal">
        <h1>Something needs a fresh start.</h1>
        <p>Your saved records are safe. Reload the workspace to try again.</p>
        <button className="btn primary" onClick={() => location.reload()}>
          Reload workspace
        </button>
      </div>
    ) : (
      this.props.children
    )
  }
}
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>,
)

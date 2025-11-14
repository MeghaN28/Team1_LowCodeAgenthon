import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useTheme } from './contexts/ThemeContext'
import Logo from './components/Logo'
import Home from './pages/Home'
import Chatbot from './pages/Chatbot'
import Dashboard from './pages/Dashboard'
import './App.css'

function Navigation() {
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  const isActive = (path) => location.pathname === path

  return (
    <nav className="navbar">
      <div className="nav-container">
        <div className="nav-logo">
          <Logo />
        </div>
        <div className="nav-right">
          <div className="nav-links">
            <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
              Inventory
            </Link>
            <Link to="/chatbot" className={`nav-link ${isActive('/chatbot') ? 'active' : ''}`}>
              Chatbot
            </Link>
            <Link to="/dashboard" className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}>
              Dashboard
            </Link>
          </div>
          <button onClick={toggleTheme} className="theme-toggle" title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  )
}

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chatbot" element={<Chatbot />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App



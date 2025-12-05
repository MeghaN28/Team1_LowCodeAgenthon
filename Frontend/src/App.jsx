import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { useTheme } from './contexts/ThemeContext';
import Logo from './components/Logo';
import Home from './pages/Home';
import Chatbot from './pages/Chatbot';
import Dashboard from './pages/Dashboard';
import UploadPurchase from './pages/UploadPurchase'; 
import ReorderLog from "./pages/ReorderLog";
// <- Import upload component
import './App.css';

function Navigation() {
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  const isActive = (path) => location.pathname === path;

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
            <Link to="/upload" className={`nav-link ${isActive('/upload') ? 'active' : ''}`}>
              Upload Purchase
            </Link>
            <Link to="/reorder-log" className={`nav-link ${isActive('/reorder-log') ? 'active' : ''}`}>
            Reorder Log
           </Link>

          </div>
          <button
            onClick={toggleTheme}
            className="theme-toggle"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          >
            {theme === 'dark' ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  );
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
            <Route path="/upload" element={<UploadPurchase />} /> {/* New upload route */}
            <Route path="/reorder-log" element={<ReorderLog />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

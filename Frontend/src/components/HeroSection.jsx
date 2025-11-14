import { useNavigate } from 'react-router-dom'

function HeroSection({ stats }) {
    const navigate = useNavigate()

    return (
        <div className="portfolio-hero-section">
            <div className="hero-content-left">
                <div className="hero-role-badge">AI-Powered Inventory Management</div>

                <p className="hero-description-text">
                    Intelligent inventory management system powered by AI that continuously monitors your stock levels
                    and automatically refills items when they run low. With advanced predictive analytics and 24/7
                    surveillance, you'll never run out of supplies again. Experience seamless automation with real-time
                    tracking and intelligent insights.
                </p>

                <div className="hero-stats-mini">
                    <div className="stat-mini">
                        <div className="stat-mini-number">{stats.total}</div>
                        <div className="stat-mini-label">Total Items</div>
                    </div>
                    <div className="stat-mini">
                        <div className="stat-mini-number">{stats.inStock}</div>
                        <div className="stat-mini-label">In Stock</div>
                    </div>
                    <div className="stat-mini">
                        <div className="stat-mini-number">{stats.lowStock}</div>
                        <div className="stat-mini-label">Low Stock</div>
                    </div>
                    <div className="stat-mini">
                        <div className="stat-mini-number">{stats.outOfStock}</div>
                        <div className="stat-mini-label">Out of Stock</div>
                    </div>
                </div>

                <div className="hero-cta-buttons">
                    <button className="cta-button primary" onClick={() => navigate('/chatbot')}>Ask AI</button>
                    <button className="cta-button secondary" onClick={() => navigate('/dashboard')}>View Dashboard </button>
                </div>
            </div>

            <div className="image-right">
                <div className="profile-image-wrapper">
                    <img
                        src="/images/img_ai.png"
                        alt="Inventory Management Illustration"
                        className="profile-image-circle"
                    />
                </div>
            </div>
        </div>
    )
}

export default HeroSection

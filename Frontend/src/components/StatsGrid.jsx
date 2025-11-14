function StatsGrid({ stats }) {
    return (
        <div className="stats-grid">
            <div className="stat-card">
                <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                    📦
                </div>
                <div className="stat-content">
                    <div className="stat-label">Total Items</div>
                    <div className="stat-value">{stats.totalItems}</div>
                </div>
            </div>

            <div className="stat-card">
                <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}>
                    ✅
                </div>
                <div className="stat-content">
                    <div className="stat-label">In Stock</div>
                    <div className="stat-value">{stats.inStock}</div>
                </div>
            </div>

            <div className="stat-card">
                <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
                    ⚠️
                </div>
                <div className="stat-content">
                    <div className="stat-label">Low Stock</div>
                    <div className="stat-value">{stats.lowStock}</div>
                </div>
            </div>

            <div className="stat-card">
                <div className="stat-icon" style={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}>
                    ❌
                </div>
                <div className="stat-content">
                    <div className="stat-label">Out of Stock</div>
                    <div className="stat-value">{stats.outOfStock}</div>
                </div>
            </div>
        </div>
    )
}

export default StatsGrid

function LowStockAlerts({ lowStockAlerts }) {
    return (
        <div className="alerts-section">
            <h2 className="section-title">Low Stock Alerts</h2>
            {lowStockAlerts.length > 0 ? (
                <div className="alerts-grid">
                    {lowStockAlerts.map(item => (
                        <div key={item.id} className="alert-card">
                            <div className="alert-icon">⚠️</div>
                            <div className="alert-content">
                                <div className="alert-item-name">{item.name}</div>
                                <div className="alert-details">
                                    Current: {item.quantity} | Threshold: {item.threshold}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="no-alerts">No low stock alerts at this time.</div>
            )}
        </div>
    )
}

export default LowStockAlerts

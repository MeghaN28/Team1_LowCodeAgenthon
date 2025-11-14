function InventoryCard({ item, index, getStockStatus, statusLabels, statusColors }) {
    const status = getStockStatus(item)
    const stockPercentage = item.threshold > 0
        ? Math.min((item.quantity / (item.threshold * 3)) * 100, 100)
        : 0

    return (
        <div
            className="portfolio-inventory-card"
            style={{ animationDelay: `${index * 0.05}s` }}
        >
            {/* Visual Area - Top */}
            <div
                className="card-visual-area"
                style={{
                    background: `linear-gradient(135deg, ${statusColors[status]}15 0%, ${statusColors[status]}05 100%)`,
                    borderBottom: `2px solid ${statusColors[status]}40`
                }}
            >
                <div className="visual-content">
                    <div className="visual-icon-wrapper">
                        <div
                            className="visual-icon"
                            style={{
                                backgroundColor: `${statusColors[status]}20`,
                                borderColor: statusColors[status]
                            }}
                        >
                            📦
                        </div>
                    </div>
                    <div className="visual-stats">
                        <div className="visual-stat-item">
                            <span className="visual-stat-label">Quantity</span>
                            <span className="visual-stat-value" style={{ color: statusColors[status] }}>
                                {item.quantity}
                            </span>
                        </div>
                        <div className="visual-stat-item">
                            <span className="visual-stat-label">Threshold</span>
                            <span className="visual-stat-value" style={{ color: statusColors[status] }}>
                                {item.threshold}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content Area - Bottom */}
            <div className="card-content-area">
                <div className="card-title-section">
                    <h3 className="card-item-title">{item.name}</h3>
                    <div className="card-tags">
                        <span className="card-tag category-tag">{item.category}</span>
                        <span
                            className="card-tag status-tag"
                            style={{
                                backgroundColor: `${statusColors[status]}20`,
                                color: statusColors[status],
                                borderColor: statusColors[status]
                            }}
                        >
                            {statusLabels[status]}
                        </span>
                    </div>
                </div>

                <p className="card-description">
                    Current stock level: <strong style={{ color: statusColors[status] }}>{item.quantity} units</strong>.
                    {status === 'in-stock' && ' Stock is healthy and well-maintained.'}
                    {status === 'low-stock' && ' Stock is running low. Auto-refill in progress.'}
                    {status === 'out-of-stock' && ' Item is out of stock. Urgent restocking required.'}
                </p>

                <div className="card-progress-section">
                    <div className="progress-header">
                        <span className="progress-label">Stock Level</span>
                        <span className="progress-value" style={{ color: statusColors[status] }}>
                            {Math.round(stockPercentage)}%
                        </span>
                    </div>
                    <div className="card-progress-bar">
                        <div
                            className="card-progress-fill"
                            style={{
                                width: `${stockPercentage}%`,
                                backgroundColor: statusColors[status]
                            }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default InventoryCard

function FilterSection({
    sortBy,
    setSortBy,
    selectedStockStatus,
    setSelectedStockStatus,
    stockStatusOptions
}) {
    return (
        <div className="filter-section">
            <div className="filter-row">
                <div className="filter-group-modern">
                    <label className="filter-label-modern">Sort By</label>
                    <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="sort-select-modern"
                    >
                        <option value="name">Name (A-Z)</option>
                        <option value="quantity">Quantity (High to Low)</option>
                        <option value="category">Category</option>
                        <option value="status">Status Priority</option>
                    </select>
                </div>

                <div className="stock-status-section">
                    <h2 className="stock-status-heading">STOCK STATUS</h2>
                    <div className="stock-status-buttons">
                        {stockStatusOptions.map(status => (
                            <button
                                key={status}
                                onClick={() => setSelectedStockStatus(status)}
                                className={`stock-status-button ${selectedStockStatus === status ? 'active' : ''} ${status === 'In Stock' ? 'status-success' :
                                        status === 'Low Stock' ? 'status-warning' :
                                            status === 'Out of Stock' ? 'status-danger' : 'status-all'
                                    }`}
                            >
                                <span className="status-icon">
                                    {status === 'All' && (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M9 2v4M15 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" />
                                        </svg>
                                    )}
                                    {status === 'In Stock' && (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                            <rect x="4" y="4" width="16" height="16" rx="2" fill="#10b981" />
                                            <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                        </svg>
                                    )}
                                    {status === 'Low Stock' && (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                                            <path d="M12 2L2 22h20L12 2z" fill="#f59e0b" />
                                            <path d="M12 8v4M12 16h.01" stroke="white" strokeWidth="2" strokeLinecap="round" />
                                        </svg>
                                    )}
                                    {status === 'Out of Stock' && (
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <circle cx="12" cy="12" r="10" fill="#ef4444" />
                                            <line x1="8" y1="8" x2="16" y2="16" stroke="white" strokeWidth="2" />
                                            <line x1="16" y1="8" x2="8" y2="16" stroke="white" strokeWidth="2" />
                                        </svg>
                                    )}
                                </span>
                                <span className="status-text">{status}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default FilterSection

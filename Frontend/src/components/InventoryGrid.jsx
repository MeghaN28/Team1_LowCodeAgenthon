import InventoryCard from './InventoryCard'

function InventoryGrid({
    filteredAndSortedInventory,
    getStockStatus,
    statusLabels,
    statusColors
}) {
    return (
        <div className="inventory-section">
            <div className="section-header">
                <h2 className="section-title-portfolio">
                    Inventory Items
                    <span className="item-count-portfolio">({filteredAndSortedInventory.length})</span>
                </h2>
            </div>
            <div className="inventory-grid">
                {filteredAndSortedInventory.map((item, index) => (
                    <InventoryCard
                        key={item.id}
                        item={item}
                        index={index}
                        getStockStatus={getStockStatus}
                        statusLabels={statusLabels}
                        statusColors={statusColors}
                    />
                ))}
            </div>

            {filteredAndSortedInventory.length === 0 && (
                <div className="empty-state-modern">
                    <div className="empty-icon-wrapper">
                        <span className="empty-icon-modern">🔍</span>
                    </div>
                    <h3 className="empty-title">No items found</h3>
                    <p className="empty-description">Try adjusting your search or filter criteria</p>
                </div>
            )}
        </div>
    )
}

export default InventoryGrid

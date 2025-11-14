function InventoryTable({
    inventory,
    editingId,
    editForm,
    setEditForm,
    categories,
    getStockStatus,
    handleEdit,
    handleSaveEdit,
    handleCancelEdit,
    handleDelete
}) {
    return (
        <div className="table-container">
            <table className="inventory-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Quantity</th>
                        <th>Threshold</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {inventory.map(item => (
                        <tr key={item.id}>
                            {editingId === item.id ? (
                                <>
                                    <td>
                                        <input
                                            type="text"
                                            value={editForm.name}
                                            onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                                            className="table-input"
                                        />
                                    </td>
                                    <td>
                                        <select
                                            value={editForm.category}
                                            onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                                            className="table-input"
                                        >
                                            {categories.map(cat => (
                                                <option key={cat} value={cat}>{cat}</option>
                                            ))}
                                        </select>
                                    </td>
                                    <td>
                                        <input
                                            type="number"
                                            value={editForm.quantity}
                                            onChange={(e) => setEditForm({ ...editForm, quantity: e.target.value })}
                                            className="table-input"
                                        />
                                    </td>
                                    <td>
                                        <input
                                            type="number"
                                            value={editForm.threshold}
                                            onChange={(e) => setEditForm({ ...editForm, threshold: e.target.value })}
                                            className="table-input"
                                        />
                                    </td>
                                    <td>
                                        <span className={`status-badge ${getStockStatus(item)}`}>
                                            {getStockStatus(item).replace('-', ' ')}
                                        </span>
                                    </td>
                                    <td>
                                        <button onClick={handleSaveEdit} className="action-button save">Save</button>
                                        <button onClick={handleCancelEdit} className="action-button cancel">Cancel</button>
                                    </td>
                                </>
                            ) : (
                                <>
                                    <td>{item.name}</td>
                                    <td>{item.category}</td>
                                    <td>{item.quantity}</td>
                                    <td>{item.threshold}</td>
                                    <td>
                                        <span className={`status-badge ${getStockStatus(item)}`}>
                                            {getStockStatus(item).replace('-', ' ')}
                                        </span>
                                    </td>
                                    <td>
                                        <button onClick={() => handleEdit(item)} className="action-button edit">Edit</button>
                                        <button onClick={() => handleDelete(item.id)} className="action-button delete">Delete</button>
                                    </td>
                                </>
                            )}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default InventoryTable

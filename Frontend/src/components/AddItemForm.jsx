function AddItemForm({ newItem, setNewItem, categories, handleAddItem }) {
    return (
        <div className="add-form">
            <input
                type="text"
                placeholder="Item Name"
                value={newItem.name}
                onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
                className="form-input"
            />
            <select
                value={newItem.category}
                onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
                className="form-input"
            >
                <option value="">Select Category</option>
                {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                ))}
            </select>
            <input
                type="number"
                placeholder="Quantity"
                value={newItem.quantity}
                onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                className="form-input"
            />
            <input
                type="number"
                placeholder="Threshold"
                value={newItem.threshold}
                onChange={(e) => setNewItem({ ...newItem, threshold: e.target.value })}
                className="form-input"
            />
            <button onClick={handleAddItem} className="save-button">
                Add Item
            </button>
        </div>
    )
}

export default AddItemForm

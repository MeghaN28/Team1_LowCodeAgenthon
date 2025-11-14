import { useState } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import StatsGrid from '../components/StatsGrid'
import ChartsSection from '../components/ChartsSection'
import LowStockAlerts from '../components/LowStockAlerts'
import AddItemForm from '../components/AddItemForm'
import InventoryTable from '../components/InventoryTable'
import './Dashboard.css'

const initialInventory = [
  { id: 1, name: 'Paracetamol 500mg', category: 'Pain Relief', quantity: 150, threshold: 50 },
  { id: 2, name: 'Ibuprofen 400mg', category: 'Pain Relief', quantity: 25, threshold: 50 },
  { id: 3, name: 'Amoxicillin 250mg', category: 'Antibiotics', quantity: 0, threshold: 30 },
  { id: 4, name: 'Aspirin 100mg', category: 'Pain Relief', quantity: 200, threshold: 50 },
  { id: 5, name: 'Insulin Vial', category: 'Diabetes', quantity: 45, threshold: 40 },
  { id: 6, name: 'Bandages', category: 'First Aid', quantity: 300, threshold: 100 },
  { id: 7, name: 'Gauze Pads', category: 'First Aid', quantity: 15, threshold: 50 },
  { id: 8, name: 'Antiseptic Solution', category: 'First Aid', quantity: 80, threshold: 50 },
  { id: 9, name: 'Metformin 500mg', category: 'Diabetes', quantity: 120, threshold: 50 },
  { id: 10, name: 'Ciprofloxacin 500mg', category: 'Antibiotics', quantity: 60, threshold: 50 },
  { id: 11, name: 'Syringes 5ml', category: 'Medical Supplies', quantity: 200, threshold: 100 },
  { id: 12, name: 'Gloves (Box)', category: 'Medical Supplies', quantity: 35, threshold: 50 },
  { id: 13, name: 'Face Masks (Box)', category: 'Medical Supplies', quantity: 500, threshold: 200 },
  { id: 14, name: 'Thermometer', category: 'Medical Equipment', quantity: 8, threshold: 10 },
  { id: 15, name: 'Blood Pressure Monitor', category: 'Medical Equipment', quantity: 12, threshold: 10 },
]

function Dashboard() {
  const { theme } = useTheme()
  const [inventory, setInventory] = useState(initialInventory)
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState({ name: '', category: '', quantity: '', threshold: '' })
  const [newItem, setNewItem] = useState({ name: '', category: '', quantity: '', threshold: '' })
  const [showAddForm, setShowAddForm] = useState(false)

  // Theme-aware colors for charts
  const chartColors = {
    dark: {
      bg: '#1e293b',
      border: '#334155',
      text: '#f1f5f9',
      textSecondary: '#cbd5e1',
      grid: '#334155'
    },
    light: {
      bg: '#ffffff',
      border: '#e2e8f0',
      text: '#1e293b',
      textSecondary: '#64748b',
      grid: '#e2e8f0'
    }
  }

  const colors = chartColors[theme]

  const getStockStatus = (item) => {
    if (item.quantity === 0) return 'out-of-stock'
    if (item.quantity <= item.threshold) return 'low-stock'
    return 'in-stock'
  }

  const stats = {
    totalItems: inventory.length,
    inStock: inventory.filter(item => item.quantity > item.threshold).length,
    lowStock: inventory.filter(item => item.quantity > 0 && item.quantity <= item.threshold).length,
    outOfStock: inventory.filter(item => item.quantity === 0).length,
    totalQuantity: inventory.reduce((sum, item) => sum + item.quantity, 0)
  }

  const categoryData = inventory.reduce((acc, item) => {
    const cat = item.category
    if (!acc[cat]) {
      acc[cat] = { name: cat, quantity: 0, items: 0 }
    }
    acc[cat].quantity += item.quantity
    acc[cat].items += 1
    return acc
  }, {})

  const categoryChartData = Object.values(categoryData).map(cat => ({
    name: cat.name,
    quantity: cat.quantity,
    items: cat.items
  }))

  const statusData = [
    { name: 'In Stock', value: stats.inStock, color: '#10b981' },
    { name: 'Low Stock', value: stats.lowStock, color: '#f59e0b' },
    { name: 'Out of Stock', value: stats.outOfStock, color: '#ef4444' }
  ]

  const consumptionData = [
    { month: 'Jan', usage: 450 },
    { month: 'Feb', usage: 520 },
    { month: 'Mar', usage: 480 },
    { month: 'Apr', usage: 610 },
    { month: 'May', usage: 550 },
    { month: 'Jun', usage: 680 }
  ]

  const lowStockAlerts = inventory.filter(item => item.quantity <= item.threshold)

  const handleEdit = (item) => {
    setEditingId(item.id)
    setEditForm({
      name: item.name,
      category: item.category,
      quantity: item.quantity.toString(),
      threshold: item.threshold.toString()
    })
  }

  const handleSaveEdit = () => {
    setInventory(inventory.map(item =>
      item.id === editingId
        ? {
          ...item,
          name: editForm.name,
          category: editForm.category,
          quantity: parseInt(editForm.quantity) || 0,
          threshold: parseInt(editForm.threshold) || 0
        }
        : item
    ))
    setEditingId(null)
    setEditForm({ name: '', category: '', quantity: '', threshold: '' })
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditForm({ name: '', category: '', quantity: '', threshold: '' })
  }

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      setInventory(inventory.filter(item => item.id !== id))
    }
  }

  const handleAddItem = () => {
    if (newItem.name && newItem.category && newItem.quantity && newItem.threshold) {
      const newId = Math.max(...inventory.map(i => i.id)) + 1
      setInventory([...inventory, {
        id: newId,
        name: newItem.name,
        category: newItem.category,
        quantity: parseInt(newItem.quantity) || 0,
        threshold: parseInt(newItem.threshold) || 0
      }])
      setNewItem({ name: '', category: '', quantity: '', threshold: '' })
      setShowAddForm(false)
    }
  }

  const categories = [...new Set(inventory.map(item => item.category))]

  return (
    <div className="dashboard-page">
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <h1 className="page-title">Dashboard</h1>
      </div>

      <StatsGrid stats={stats} />

      <ChartsSection
        categoryChartData={categoryChartData}
        statusData={statusData}
        consumptionData={consumptionData}
        colors={colors}
      />

      <LowStockAlerts lowStockAlerts={lowStockAlerts} />

      <div className="management-section">
        <div className="section-header">
          <h2 className="section-title">Inventory Management</h2>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="add-button"
          >
            {showAddForm ? 'Cancel' : '+ Add New Item'}
          </button>
        </div>

        {showAddForm && (
          <AddItemForm
            newItem={newItem}
            setNewItem={setNewItem}
            categories={categories}
            handleAddItem={handleAddItem}
          />
        )}

        <InventoryTable
          inventory={inventory}
          editingId={editingId}
          editForm={editForm}
          setEditForm={setEditForm}
          categories={categories}
          getStockStatus={getStockStatus}
          handleEdit={handleEdit}
          handleSaveEdit={handleSaveEdit}
          handleCancelEdit={handleCancelEdit}
          handleDelete={handleDelete}
        />
      </div>
    </div>
  )
}

export default Dashboard



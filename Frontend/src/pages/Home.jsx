import { useState, useMemo } from 'react'
import './Home.css'
import HeroSection from '../components/HeroSection'
import SearchBar from '../components/SearchBar'
import FilterSection from '../components/FilterSection'
import InventoryGrid from '../components/InventoryGrid'

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

function Home() {
  const [inventory, setInventory] = useState(initialInventory)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStockStatus, setSelectedStockStatus] = useState('All')
  const [sortBy, setSortBy] = useState('name')
  const stockStatusOptions = ['All', 'In Stock', 'Low Stock', 'Out of Stock']

  const statusLabels = {
    'in-stock': 'In Stock',
    'low-stock': 'Low Stock',
    'out-of-stock': 'Out of Stock'
  }

  const getStockStatus = (item) => {
    if (item.quantity === 0) return 'out-of-stock'
    if (item.quantity <= item.threshold) return 'low-stock'
    return 'in-stock'
  }

  const filteredAndSortedInventory = useMemo(() => {
    let filtered = inventory.filter(item => {
      const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase())
      const status = getStockStatus(item)
      const statusLabel = statusLabels[status]
      const matchesStockStatus = selectedStockStatus === 'All' || statusLabel === selectedStockStatus
      return matchesSearch && matchesStockStatus
    })

    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name)
        case 'quantity':
          return b.quantity - a.quantity
        case 'category':
          return a.category.localeCompare(b.category)
        case 'status':
          const statusOrder = { 'out-of-stock': 0, 'low-stock': 1, 'in-stock': 2 }
          return statusOrder[getStockStatus(a)] - statusOrder[getStockStatus(b)]
        default:
          return 0
      }
    })

    return filtered
  }, [inventory, searchTerm, selectedStockStatus, sortBy])

  const statusColors = {
    'in-stock': '#10b981',
    'low-stock': '#f59e0b',
    'out-of-stock': '#ef4444'
  }

  // Calculate stats
  const stats = {
    total: inventory.length,
    inStock: inventory.filter(item => getStockStatus(item) === 'in-stock').length,
    lowStock: inventory.filter(item => getStockStatus(item) === 'low-stock').length,
    outOfStock: inventory.filter(item => getStockStatus(item) === 'out-of-stock').length
  }

  return (
    <div className="home-page">
      <HeroSection stats={stats} />

      <div className="search-filter-section">
        <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
        <FilterSection
          sortBy={sortBy}
          setSortBy={setSortBy}
          selectedStockStatus={selectedStockStatus}
          setSelectedStockStatus={setSelectedStockStatus}
          stockStatusOptions={stockStatusOptions}
        />
      </div>

      <InventoryGrid
        filteredAndSortedInventory={filteredAndSortedInventory}
        getStockStatus={getStockStatus}
        statusLabels={statusLabels}
        statusColors={statusColors}
      />
    </div>
  )
}

export default Home



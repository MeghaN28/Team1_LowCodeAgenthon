import { useState, useEffect, useMemo } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import StatsGrid from '../components/StatsGrid';
import ChartsSection from '../components/ChartsSection';
import LowStockAlerts from '../components/LowStockAlerts';
import AddItemForm from '../components/AddItemForm';
import InventoryTable from '../components/InventoryTable';
import ItemForecastModal from '../pages/ItemForecastModal';
import './Dashboard.css';

function Dashboard() {
  const { theme } = useTheme();

  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', category: '', quantity: '', threshold: '' });
  const [newItem, setNewItem] = useState({ name: '', category: '', quantity: '', threshold: '' });
  const [showAddForm, setShowAddForm] = useState(false);

  const [selectedItemSearch, setSelectedItemSearch] = useState('');
  const [agentResponse, setAgentResponse] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [currentItem, setCurrentItem] = useState(null);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  const [parsedData, setParsedData] = useState(null);

  // iGentic Config
  const IGENTIC_ORCHESTRATOR_ID = "df6578f6-7485-4946-85d3-0c6c1fb9114e";
  const IGENTIC_ENDPOINT_BASE = "https://container-hackathon-sk.salmonpebble-59bd07ab.eastus.azurecontainerapps.io/api/iGenticAutonomousAgent/Executor";
  const IGENTIC_URL = `${IGENTIC_ENDPOINT_BASE}/${IGENTIC_ORCHESTRATOR_ID}`;
  const IGENTIC_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_IGENTIC_TOKEN"
  };

  const parseAgentResponse = (text, item) => {
    if (!text) return { currentStock: item.quantity, reorderLevel: item.threshold, lowStock: false, actions: [] };

    let currentStock = item.quantity;
    let reorderLevel = item.threshold;
    let lowStock = item.quantity <= item.threshold;
    let actions = [];

    const stockMatch = text.match(/Current Stock on Hand:\s*(\d+)/i);
    if (stockMatch) currentStock = parseInt(stockMatch[1]);

    const reorderMatch = text.match(/Minimum Stock Limit:\s*(\d+)/i);
    if (reorderMatch) reorderLevel = parseInt(reorderMatch[1]);

    const lowMatch = text.match(/Low-Stock Warning:\s*(Yes|No)/i);
    lowStock = lowMatch ? lowMatch[1].toLowerCase() === "yes" : lowStock;

    const actionBlock = text.match(/Recommended Actions:[\s\S]*/i);
    if (actionBlock) {
      actions = actionBlock[0]
        .split("\n")
        .filter((l) => l.trim().startsWith("-"))
        .map((l) => l.replace("-", "").trim());
    }

    return { currentStock, reorderLevel, lowStock, actions };
  };

  // Convert value to number safely
  const safeNumber = (val) => {
    const n = Number(val);
    return isNaN(n) ? 0 : n;
  };

  // Stock status
  const getStockStatus = (item) => {
    const qty = safeNumber(item.quantity);
    const th = safeNumber(item.threshold);
    if (qty === 0) return 'out-of-stock';
    if (qty > 0 && qty <= th) return 'low-stock';
    return 'in-stock';
  };

  // Fetch inventory
  useEffect(() => {
    setLoading(true);
    fetch("http://127.0.0.1:8080/api/inventory")
      .then(res => res.json())
      .then(data => {
        if (data.success && Array.isArray(data.items)) {
          const formatted = data.items.map(item => ({
            id: item.inventory_id || `INV${Math.floor(Math.random()*100000)}`,
            name: item.item_name || 'Unnamed Item',
            category: item.item_type || item.category || 'Unknown',
            quantity: safeNumber(item.current_stock ?? item.initial_stock ?? 0),
            threshold: safeNumber(item.min_stock ?? item.minimum_required ?? 0),
            raw: item
          }));
          setInventory(formatted);
        } else {
          setInventory([]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch inventory:", err);
        setInventory([]);
        setLoading(false);
      });
  }, []);

  const chartColors = {
    dark: { bg: '#1e293b', border: '#334155', text: '#f1f5f9', textSecondary: '#cbd5e1', grid: '#334155' },
    light: { bg: '#ffffff', border: '#e2e8f0', text: '#1e293b', textSecondary: '#64748b', grid: '#e2e8f0' }
  };
  const colors = chartColors[theme] || chartColors.light;

  const handleEdit = (item) => {
    setEditingId(item.id);
    setEditForm({
      name: item.name,
      category: item.category,
      quantity: item.quantity.toString(),
      threshold: item.threshold.toString()
    });
  };

  const handleSaveEdit = () => {
    setInventory(inventory.map(item =>
      item.id === editingId
        ? { ...item, name: editForm.name, category: editForm.category, quantity: safeNumber(editForm.quantity), threshold: safeNumber(editForm.threshold) }
        : item
    ));
    setEditingId(null);
    setEditForm({ name: '', category: '', quantity: '', threshold: '' });
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditForm({ name: '', category: '', quantity: '', threshold: '' });
  };

  const categories = [...new Set(inventory.map(item => item.category))];

  const filteredInventory = useMemo(() => {
    let data = inventory;
    if (selectedItemSearch) {
      data = data.filter(item => item.name.toLowerCase().includes(selectedItemSearch.toLowerCase()));
    }
    return data;
  }, [inventory, selectedItemSearch]);

  const totalPages = Math.ceil(filteredInventory.length / itemsPerPage);
  const paginatedInventory = filteredInventory.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  // Stats: match Home page
  const stats = {
    totalItems: inventory.length,
    inStock: inventory.filter(item => getStockStatus(item) === 'in-stock').length,
    lowStock: inventory.filter(item => getStockStatus(item) === 'low-stock').length,
    outOfStock: inventory.filter(item => getStockStatus(item) === 'out-of-stock').length,
    totalQuantity: inventory.reduce((sum, item) => sum + safeNumber(item.quantity), 0)
  };

  const categoryData = inventory.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = { name: item.category, quantity: 0, items: 0 };
    acc[item.category].quantity += safeNumber(item.quantity);
    acc[item.category].items += 1;
    return acc;
  }, {});

  const categoryChartData = Object.values(categoryData).map(cat => ({
    name: cat.name,
    quantity: cat.quantity,
    items: cat.items
  }));

  const statusData = [
    { name: 'In Stock', value: stats.inStock, color: '#10b981' },
    { name: 'Low Stock', value: stats.lowStock, color: '#f59e0b' },
    { name: 'Out of Stock', value: stats.outOfStock, color: '#ef4444' }
  ];

  const lowStockAlerts = inventory.filter(item => getStockStatus(item) === 'low-stock');

  async function sendToAgent(item) {
    if (!item) return;
    setCurrentItem(item);
    setAgentLoading(true);
    setAgentError(null);
    setAgentResponse(null);
    setShowModal(false);
    setParsedData(null);

    try {
      const payload = {
        UserInput: JSON.stringify({
          item_id: item.id,
          item_name: item.name,
          forecast_output: [],
          threshold_status: {
            flag_below_min: item.quantity <= item.threshold,
            reorder_level: item.threshold,
            reason: item.quantity <= item.threshold ? "Below minimum" : "Stock OK"
          },
          stock_info: {
            Closing_Stock: item.quantity,
            Min_Stock_Limit: item.threshold,
            Vendor: { vendor_name: item.raw.vendor_name || "Vendor_ABC" }
          },
          prompt: `Generate a detailed forecast report for ${item.name}, including consumption trends, low-stock warnings, and recommended actions.`
        }),
        sessionId: localStorage.getItem("igentic_session") || "",
        executionId: crypto.randomUUID ? crypto.randomUUID() : (Date.now().toString() + Math.random().toString()),
        connectionID: "react-frontend",
        isImage: false,
        base64string: "",
        evalId: "",
        userInputType: ""
      };

      const res = await fetch(IGENTIC_URL, {
        method: "POST",
        headers: IGENTIC_HEADERS,
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`iGentic API error: ${res.status} ${txt}`);
      }

      const data = await res.json();

      if (data.session_id) localStorage.setItem("igentic_session", data.session_id);

      setAgentResponse(data);

      const parsed = parseAgentResponse(data.result || "", item);

      setParsedData(parsed);
      setShowModal(true);

    } catch (err) {
      console.error(err);
      setAgentError(err.message || String(err));
    } finally {
      setAgentLoading(false);
    }
  }

  const handleSendToAgent = async (item) => {
    await sendToAgent(item);
  };

  if (loading) return <div className="loading">Loading inventory...</div>;

  return (
    <div className="dashboard-page">
      <div className="page-header" style={{ marginBottom: '1rem' }}>
        <h1 className="page-title">Dashboard</h1>
        <div className="agent-search-section" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <input
            type="text"
            placeholder="Search item..."
            value={selectedItemSearch}
            onChange={e => setSelectedItemSearch(e.target.value)}
            style={{ padding: '0.5rem', width: '300px' }}
          />
          <button
            onClick={() => {
              if (filteredInventory.length > 0) handleSendToAgent(filteredInventory[0]);
              else alert("No item selected or available.");
            }}
            style={{ padding: '0.5rem 1rem', cursor: 'pointer', background: '#4facfe', color: 'white', borderRadius: '8px' }}
          >
            Send to Agent
          </button>
        </div>
      </div>

      <StatsGrid stats={stats} />
      <ChartsSection
        categoryChartData={categoryChartData}
        statusData={statusData}
        colors={colors}
      />
      <LowStockAlerts lowStockAlerts={lowStockAlerts} />

      <div className="management-section">
        <div className="section-header">
          <h2 className="section-title">Inventory Management</h2>
          <button onClick={() => setShowAddForm(!showAddForm)} className="add-button">
            {showAddForm ? 'Cancel' : '+ Add New Item'}
          </button>
        </div>

        {showAddForm && (
          <AddItemForm
            newItem={newItem}
            setNewItem={setNewItem}
            categories={categories}
            handleAddItem={() => {
              const nextId = `INV${(Math.random()*100000).toFixed(0)}`;
              const created = {
                id: nextId,
                name: newItem.name || 'New Item',
                category: newItem.category || 'Unknown',
                quantity: safeNumber(newItem.quantity),
                threshold: safeNumber(newItem.threshold)
              };
              setInventory([created, ...inventory]);
              setShowAddForm(false);
              setNewItem({ name: '', category: '', quantity: '', threshold: '' });
            }}
          />
        )}

        <InventoryTable
          inventory={paginatedInventory}
          editingId={editingId}
          editForm={editForm}
          setEditForm={setEditForm}
          categories={categories}
          getStockStatus={getStockStatus}
          handleEdit={handleEdit}
          handleSaveEdit={handleSaveEdit}
          handleCancelEdit={handleCancelEdit}
          handleDelete={id => setInventory(inventory.filter(it => it.id !== id))}
        />

        {totalPages > 1 && (
          <div className="pagination-controls">
            <button onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} disabled={currentPage === 1}>
              &lt; Prev
            </button>
            {[...Array(totalPages)].map((_, i) => (
              <button
                key={i}
                className={currentPage === i + 1 ? 'active' : ''}
                onClick={() => setCurrentPage(i + 1)}
              >
                {i + 1}
              </button>
            ))}
            <button onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages}>
              Next &gt;
            </button>
          </div>
        )}
      </div>

      {showModal && (
        <ItemForecastModal
          item={currentItem}
          parsed={parsedData}
          onClose={() => {
            setShowModal(false);
            setCurrentItem(null);
            setParsedData(null);
          }}
        />
      )}
    </div>
  );
}

export default Dashboard;

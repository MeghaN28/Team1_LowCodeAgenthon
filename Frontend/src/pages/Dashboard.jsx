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
  // =========================
  // Hooks (Top Level Only)
  // =========================
  const { theme } = useTheme();

  // Inventory state
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', category: '', quantity: '', threshold: '' });
  const [newItem, setNewItem] = useState({ name: '', category: '', quantity: '', threshold: '' });
  const [showAddForm, setShowAddForm] = useState(false);

  // Search & Agent state
  const [selectedItemSearch, setSelectedItemSearch] = useState('');
  const [selectedItemId, setSelectedItemId] = useState('');

  const [agentResponse, setAgentResponse] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [agentError, setAgentError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [parsedData, setParsedData] = useState(null);

  // =========================
  // Fetch Inventory
  // =========================
  useEffect(() => {
    fetch("http://127.0.0.1:8080/api/inventory")
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          const formatted = data.items.map(item => ({
            id: item.inventory_id,
            name: item.item_name,
            category: item.item_type || 'Unknown',
            quantity: item.current_stock || item.initial_stock || 0,
            threshold: item.min_stock || item.minimum_required || 0,
            raw: item
          }));
          setInventory(formatted);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  // =========================
  // Theme Colors
  // =========================
  const chartColors = {
    dark: { bg: '#1e293b', border: '#334155', text: '#f1f5f9', textSecondary: '#cbd5e1', grid: '#334155' },
    light: { bg: '#ffffff', border: '#e2e8f0', text: '#1e293b', textSecondary: '#64748b', grid: '#e2e8f0' }
  };
  const colors = chartColors[theme];

  // =========================
  // Helper Functions
  // =========================
  const getStockStatus = (item) => {
    if (item.quantity === 0) return 'out-of-stock';
    if (item.quantity <= item.threshold) return 'low-stock';
    return 'in-stock';
  };

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
        ? { ...item, name: editForm.name, category: editForm.category, quantity: parseInt(editForm.quantity) || 0, threshold: parseInt(editForm.threshold) || 0 }
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

  // =========================
  // Derived / Memoized Data
  // =========================
  const filteredSearchItems = useMemo(() => {
    if (!selectedItemSearch) return inventory;
    return inventory.filter(item => item.name.toLowerCase().includes(selectedItemSearch.toLowerCase()));
  }, [inventory, selectedItemSearch]);

  const uniqueLowStock = useMemo(() => {
    const seen = new Set();
    return inventory.filter(item => {
      if (item.quantity <= item.threshold && !seen.has(item.name)) {
        seen.add(item.name);
        return true;
      }
      return false;
    });
  }, [inventory]);

  const stats = {
    totalItems: inventory.length,
    inStock: inventory.filter(item => item.quantity > item.threshold).length,
    lowStock: inventory.filter(item => item.quantity > 0 && item.quantity <= item.threshold).length,
    outOfStock: inventory.filter(item => item.quantity === 0).length,
    totalQuantity: inventory.reduce((sum, item) => sum + item.quantity, 0)
  };

  const categoryData = inventory.reduce((acc, item) => {
    if (!acc[item.category]) acc[item.category] = { name: item.category, quantity: 0, items: 0 };
    acc[item.category].quantity += item.quantity;
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

  const consumptionData = [
    { month: 'Jan', usage: 450 },
    { month: 'Feb', usage: 520 },
    { month: 'Mar', usage: 480 },
    { month: 'Apr', usage: 610 },
    { month: 'May', usage: 550 },
    { month: 'Jun', usage: 680 }
  ];

  const lowStockAlerts = inventory.filter(item => item.quantity <= item.threshold);

  // =========================
  // iGentic Agent Integration
  // =========================
  const IGENTIC_ORCHESTRATOR_ID = "df6578f6-7485-4946-85d3-0c6c1fb9114e";
  const IGENTIC_ENDPOINT_BASE = "https://container-hackathon-sk.salmonpebble-59bd07ab.eastus.azurecontainerapps.io/api/iGenticAutonomousAgent/Executor";
  const IGENTIC_URL = `${IGENTIC_ENDPOINT_BASE}/${IGENTIC_ORCHESTRATOR_ID}`;
  const IGENTIC_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_IGENTIC_TOKEN"
  };

  const parseAgentResponse = (text, item) => {
    let currentStock = item.quantity;
    let reorderLevel = item.threshold;
    let lowStock = item.quantity <= item.threshold;
    let actions = [];

    const stockMatch = text.match(/Current Stock on Hand:\s*(\d+)/i);
    if (stockMatch) currentStock = parseInt(stockMatch[1]);

    const reorderMatch = text.match(/reorder level of (\d+)/i);
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

  async function sendToAgent(item) {
    if (!item) return;
    setAgentLoading(true);
    setAgentError(null);
    setAgentResponse(null);
    setShowModal(false);
    setParsedData(null);
    setSelectedItemId(item.id);

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

      const parsed = parseAgentResponse(data.result, item);
      setParsedData(parsed);
      setShowModal(true);
    } catch (err) {
      console.error(err);
      setAgentError(err.message || String(err));
    } finally {
      setAgentLoading(false);
    }
  }

  if (loading) return <div className="loading">Loading inventory...</div>;

  // =========================
  // Render
  // =========================
  return (
    <div className="dashboard-page">
      {/* iGentic Response Panel */}
      <div className="agent-response-panel">
        <h3 className="section-title">Your SupplySoul Assistant</h3>
        {agentError && <div className="agent-error">Error: {agentError}</div>}
        {agentLoading && <div className="agent-loading">Waiting for agent response...</div>}
        {agentResponse && (
          <div className="agent-response-card">
            <pre>{agentResponse.result || JSON.stringify(agentResponse, null, 2)}</pre>
          </div>
        )}
      </div>

      {/* Pop-up Modal */}
      {showModal && parsedData && selectedItemId && (
        <ItemForecastModal
          item={inventory.find(i => i.id === selectedItemId)}
          parsed={parsedData}
          onClose={() => setShowModal(false)}
        />
      )}

      {/* Dashboard Header */}
      <div className="page-header" style={{ marginBottom: '1rem' }}>
        <h1 className="page-title">Dashboard</h1>
        <div className="agent-search-section" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <input
            type="text"
            placeholder="Search item to send to agent..."
            value={selectedItemSearch}
            onChange={e => setSelectedItemSearch(e.target.value)}
            style={{ padding: '0.5rem', width: '300px' }}
          />
          <button
            onClick={() => {
              if (filteredSearchItems.length > 0) sendToAgent(filteredSearchItems[0]);
            }}
            style={{ padding: '0.5rem' }}
            disabled={filteredSearchItems.length === 0 || agentLoading}
          >
            {agentLoading ? 'Sending...' : 'Send to Agent'}
          </button>
        </div>
      </div>

      <StatsGrid stats={stats} />
      <ChartsSection
        categoryChartData={categoryChartData}
        statusData={statusData}
        consumptionData={consumptionData}
        colors={colors}
      />
      <LowStockAlerts lowStockAlerts={uniqueLowStock} />

      {/* Inventory Management */}
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
                quantity: parseInt(newItem.quantity) || 0,
                threshold: parseInt(newItem.threshold) || 0
              };
              setInventory([created, ...inventory]);
              setShowAddForm(false);
              setNewItem({ name: '', category: '', quantity: '', threshold: '' });
            }}
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
          handleDelete={id => setInventory(inventory.filter(it => it.id !== id))}
        />
      </div>
    </div>
  );
}

export default Dashboard;

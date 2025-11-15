import { Line, Bar } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend } from 'chart.js'
import './ItemForecastModal.css'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend)

export default function ItemForecastModal({ item, forecastData, onClose }) {
  if (!item || !forecastData) return null

  const { stock_history, demand_forecast } = forecastData

  const stockData = {
    labels: stock_history.map(s => s.month),
    datasets: [
      {
        label: 'Stock',
        data: stock_history.map(s => s.stock),
        backgroundColor: stock_history.some(s => s.stock <= item.threshold) ? 'rgba(255,0,0,0.5)' : 'rgba(16,185,129,0.5)',
        borderColor: stock_history.some(s => s.stock <= item.threshold) ? 'red' : 'green',
        borderWidth: 2,
      }
    ]
  }

  const demandData = {
    labels: demand_forecast.map(s => s.month),
    datasets: [
      {
        label: 'Forecasted Demand',
        data: demand_forecast.map(s => s.demand),
        backgroundColor: 'rgba(59,130,246,0.5)',
        borderColor: 'blue',
        borderWidth: 2,
      }
    ]
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <h2>{item.name} - Stock & Demand Forecast</h2>
        <button className="close-btn" onClick={onClose}>X</button>

        <div className="chart-container">
          <h4>Stock Levels</h4>
          <Bar data={stockData} />
        </div>

        <div className="chart-container">
          <h4>Demand Forecast</h4>
          <Line data={demandData} />
        </div>

        {item.quantity <= item.threshold && (
          <div className="stock-alert">
            ⚠️ Stock is below threshold! ({item.quantity} / {item.threshold})
          </div>
        )}
      </div>
    </div>
  )
}

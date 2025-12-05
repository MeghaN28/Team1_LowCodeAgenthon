import { useEffect, useState } from "react";
import "./ReorderLog.css";

export default function ReorderLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchReorderLogs = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8080/api/reorder-log"); 
      const data = await response.json();
      setLogs(data);
    } catch (err) {
      console.error("Error fetching reorder logs:", err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchReorderLogs();
  }, []);

  return (
    <div className="reorder-container">
      <h2 className="reorder-title">Reorder Log</h2>

      {loading ? (
        <p className="loading">Loading reorder logs...</p>
      ) : logs.length === 0 ? (
        <p className="no-data">No reorder logs found.</p>
      ) : (
        <table className="reorder-table">
          <thead>
            <tr>
              <th>Log ID</th>
              <th>Item Name</th>
              <th>Inventory ID</th>
              <th>Reorder Qty</th>
              <th>Current Stock</th>
              <th>Status</th>
              <th>Email Recipient</th>
              <th>Email Subject</th>
              <th>Email Body</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.log_id}>
                <td>{log.log_id}</td>
                <td>{log.item_name}</td>
                <td>{log.inventory_id}</td>
                <td>{log.reorder_quantity}</td>
                <td>{log.current_stock}</td>
                <td className={`status ${log.status.toLowerCase()}`}>
                  {log.status}
                </td>
                <td>{log.email_recipient || "-"}</td>
                <td>{log.email_subject || "-"}</td>
                <td className="email-body">{log.email_body || "-"}</td>
                <td>{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

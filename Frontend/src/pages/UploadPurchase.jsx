import { useState } from 'react';
import './UploadPurchase.css';

export default function PurchaseUpload() {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [agentResponse, setAgentResponse] = useState(null);

  const AGENT_ID = "612e3775-c2a3-40a5-b9ff-016be034a246";
  const IGENTIC_ENDPOINT_BASE = "https://container-hackathon-sk.salmonpebble-59bd07ab.eastus.azurecontainerapps.io/api/iGenticAutonomousAgent/Executor";
  const IGENTIC_URL = `${IGENTIC_ENDPOINT_BASE}/${AGENT_ID}`;
  const IGENTIC_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_IGENTIC_TOKEN"  // replace with your token
  };

  const handleFileChange = (e) => {
    setFiles([...e.target.files]);
    setUploadedFiles([]);
    setError(null);
    setAgentResponse(null);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setLoading(true);
    setError(null);
    setUploadedFiles([]);
    setAgentResponse(null);

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      // Upload files
      const res = await fetch("http://localhost:8080/api/purchase/upload_bulk", {
        method: "POST",
        body: formData
      });
      const data = await res.json();

      if (!data.success) {
        setError(data.error || "Upload failed");
        return;
      }
      setUploadedFiles(data.files);

      // Trigger agent
      const promptPayload = {
        UserInput: `Please process all uploaded purchase receipts stored in ~/Documents/receipts. 
For each receipt:
- Extract item names and quantities
- Use the Inventory & Demand MCP tools to update inventory_master and consumption tables
- Fetch current stock status and suggested alternatives if items are low or out of stock

Return a summary per receipt, including items processed, quantities consumed, updated stock, and alternatives.`,
        base64string: "",
        additionalData: {
          receipts_path: "/home/meghanarendrasimha/Documents/receipts"
        }
      };

      const agentRes = await fetch(IGENTIC_URL, {
        method: "POST",
        headers: IGENTIC_HEADERS,
        body: JSON.stringify(promptPayload)
      });

      const agentData = await agentRes.json();
      setAgentResponse(agentData);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Helper to render receipt summaries nicely
  const renderReceipts = () => {
    if (!agentResponse?.success || !agentResponse.receipts_summary) return null;

    return agentResponse.receipts_summary.map((receipt, idx) => (
      <div key={idx} className="receipt-card">
        <h4>Receipt: {receipt.filename}</h4>
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Quantity Consumed</th>
              <th>Previous Stock</th>
              <th>Updated Stock</th>
              <th>Stock Status</th>
              <th>Alternatives</th>
            </tr>
          </thead>
          <tbody>
            {receipt.processed_items.map((item, iidx) => (
              <tr key={iidx}>
                <td>{item.item}</td>
                <td>{item.quantity_consumed || '-'}</td>
                <td>{item.Previous_Stock || '-'}</td>
                <td>{item.Updated_Stock || '-'}</td>
                <td>{item.Stock_Status || item.status}</td>
                <td>{item.Alternatives || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ));
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <h2>Upload Purchase Receipts (Bulk)</h2>
        <div className="upload-section">
          <input
            type="file"
            accept="image/*,application/pdf"
            multiple
            onChange={handleFileChange}
          />
          <button
            onClick={handleUpload}
            disabled={files.length === 0 || loading}
          >
            {loading ? "Uploading & Triggering Agent..." : "Upload & Process"}
          </button>
        </div>

        {error && <p className="error-msg">{error}</p>}

        {uploadedFiles.length > 0 && (
          <div className="uploaded-files">
            <h3>Uploaded Files:</h3>
            <ul>
              {uploadedFiles.map((f, idx) => (
                <li key={idx}>{f}</li>
              ))}
            </ul>
          </div>
        )}

        {agentResponse && (
          <div className="orchestrator-response">
            <h3>Agent Trigger Response:</h3>
            {renderReceipts() || (
              <pre className="beautified-response">
                {agentResponse.result || JSON.stringify(agentResponse, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// run_recipt_agent.js
// Node 18+ / 24+ has global fetch, no need for node-fetch

const AGENT_ID = "612e3775-c2a3-40a5-b9ff-016be034a246";
const IGENTIC_ENDPOINT_BASE = "https://container-hackathon-sk.salmonpebble-59bd07ab.eastus.azurecontainerapps.io/api/iGenticAutonomousAgent/Executor";
const IGENTIC_URL = `${IGENTIC_ENDPOINT_BASE}/${AGENT_ID}`;
const IGENTIC_HEADERS = {
  "Content-Type": "application/json",
  "Authorization": "Bearer YOUR_IGENTIC_TOKEN"  // replace with your token
};

const promptPayload = {
  UserInput: `Please process all uploaded purchase receipts stored in ~/Documents/receipts. 
For each receipt:
- Extract item names and quantities
- Use the Inventory & Demand MCP tools to update inventory_master and consumption tables
- Fetch current stock status and suggested alternatives if items are low or out of stock

Return a summary per receipt, including items processed, quantities consumed, updated stock, and alternatives.`,
  base64string: "",
  additionalData: {
    receipts_path: "/Users/meghanarendrasimha/Documents/receipts"
  }
};

async function runReceiptAgent() {
  try {
    console.log("Triggering receipt processing agent...");

    const response = await fetch(IGENTIC_URL, {
      method: "POST",
      headers: IGENTIC_HEADERS,
      body: JSON.stringify(promptPayload)
    });

    if (!response.ok) {
      console.error(`Agent call failed: ${response.status} ${response.statusText}`);
      return;
    }

    const data = await response.json();
    console.log("Agent response:", JSON.stringify(data, null, 2));

  } catch (err) {
    console.error("Error calling receipt agent:", err);
  }
}

// Run the agent
runReceiptAgent();

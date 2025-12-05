// send_reminder_email.mjs
import pkg from 'pg';
const { Client } = pkg;

const IGENTIC_HEADERS = {
  "Content-Type": "application/json",
  "Authorization": "Bearer YOUR_IGENTIC_TOKEN"  // replace with your token
};

const REORDER_AGENT_URL = "https://container-hackathon-sk.salmonpebble-59bd07ab.eastus.azurecontainerapps.io/api/iGenticAutonomousAgent/Executor/f800f4c2-eb25-467c-942b-b81de85e2f1c";

// -------------------------------
// Connect to PostgreSQL
// -------------------------------
const client = new Client({
  host: "localhost",
  port: 5432,
  database: "medical_inventory_db",
  user: "meghanarendrasimha",
  password: "Welcome@123"
});

// -------------------------------
// Get pending reorders older than 2 days with low stock
// -------------------------------
async function getPendingReorders() {
  await client.connect();

  const query = `
    SELECT r.inventory_id, r.item_name, r.reorder_quantity, r.current_stock, i.min_stock, i.closing_stock
    FROM reorder_log r
    JOIN inventory_master i ON r.inventory_id = i.inventory_id
    WHERE r.created_at < NOW() - INTERVAL '2 days'
      AND i.closing_stock < i.min_stock
  `;

  const res = await client.query(query);
  await client.end();
  return res.rows;
}

// -------------------------------
// Send reorder follow-up email via MCP
// -------------------------------
async function sendFollowUpEmail(item) {
  const { inventory_id, item_name, reorder_quantity, current_stock } = item;

  const payload = {
    UserInput: `Please send follow-up reorder email for item: ${item_name} (Inventory ID: ${inventory_id}). Current stock is ${current_stock}, reorder quantity: ${reorder_quantity}.`,
    base64string: "",
    additionalData: {}
  };

  const response = await fetch(REORDER_AGENT_URL, {
    method: "POST",
    headers: IGENTIC_HEADERS,
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    console.error(`Failed to trigger follow-up for ${item_name}: ${response.statusText}`);
    return;
  }

  const data = await response.json();
  console.log(`Follow-up triggered for ${item_name}:`, JSON.stringify(data, null, 2));
}

// -------------------------------
// Main function
// -------------------------------
async function triggerReorderFollowUps() {
  try {
    console.log("Checking pending reorders older than 2 days with low stock...");

    const pendingItems = await getPendingReorders();

    if (pendingItems.length === 0) {
      console.log("No pending reorders found.");
      return;
    }

    for (const item of pendingItems) {
      await sendFollowUpEmail(item);
    }

  } catch (err) {
    console.error("Error in reorder follow-ups:", err);
  }
}

// -------------------------------
// Run
// -------------------------------
triggerReorderFollowUps();

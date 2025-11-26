# combined_mcp_demand_stock.py
# ---------------------------------------
# MCP Agent for Inventory Data + Demand Forecast + Dashboard Report
# Handles multiple inventory IDs per item, stock warnings, low-stock prioritization,
# and automatic alternative recommendations
# ---------------------------------------

import psycopg2
import pandas as pd
import numpy as np
from fastmcp import FastMCP
from thefuzz import fuzz, process
import re
from sentence_transformers import SentenceTransformer
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import pickle
import base64
# ----------------------------
# Initialize MCP
# ----------------------------
mcp = FastMCP("Inventory & Demand MCP 📦🧠")

# ----------------------------
# PostgreSQL setup
# ----------------------------
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="inventory_database",
    user="meghanarendrasimha",
    password="Welcome@123"
)
cur = conn.cursor()

# ----------------------------
# Load inventory_master names from DB
# ----------------------------
def load_inventory_master_names():
    cur.execute("SELECT inventory_id, item_name FROM inventory_master")
    rows = cur.fetchall()
    master_map = {}
    for r in rows:
        inv_id = str(r[0]).strip()
        name = r[1] or ""
        master_map.setdefault(name, []).append(inv_id)
    return master_map

inventory_master_map = load_inventory_master_names()

# ----------------------------
# Normalize text
# ----------------------------
def normalize_text(s: str):
    if not s:
        return ""
    s = str(s).replace('\xa0', ' ').lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

master_name_to_ids = {normalize_text(k): v for k, v in inventory_master_map.items()}
inventory_ids_set = set([iid for ids in inventory_master_map.values() for iid in ids])

# ----------------------------
# Semantic search setup
# ----------------------------
sem_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 384-dim

def load_inventory_embeddings():
    cur.execute("SELECT inventory_id, embedding FROM inventory_master WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    emb_map = {}
    for inv_id, emb in rows:
        if emb:
            if isinstance(emb, str):
                emb = np.fromstring(emb.strip('[]'), sep=',', dtype=np.float32)
            emb_map[str(inv_id)] = np.array(emb, dtype=np.float32)
    return emb_map

inventory_embeddings = load_inventory_embeddings()
inventory_ids = list(inventory_embeddings.keys())
emb_matrix = np.stack(list(inventory_embeddings.values())) if inventory_embeddings else np.zeros((0,384), dtype=np.float32)

def semantic_search(query: str, top_k: int = 1, threshold: float = 0.6):
    if len(inventory_embeddings) == 0:
        return None, 0.0
    query_emb = sem_model.encode(query)
    query_emb = np.array(query_emb, dtype=np.float32)
    emb_norms = np.linalg.norm(emb_matrix, axis=1) * np.linalg.norm(query_emb)
    sims = np.dot(emb_matrix, query_emb) / (emb_norms + 1e-10)
    best_idx = np.argmax(sims)
    best_score = sims[best_idx]
    if best_score >= threshold:
        return inventory_ids[best_idx], best_score
    return None, 0.0

# ----------------------------
# Resolve inventory IDs
# ----------------------------
def resolve_inventory_ids(input_str: str):
    if not input_str:
        return []

    raw = str(input_str).strip()
    input_upper = raw.upper()
    input_clean = normalize_text(raw)

    resolved = []

    if input_upper in inventory_ids_set:
        resolved.append((input_upper, "Exact Inventory_ID"))

    if input_clean in master_name_to_ids:
        for iid in master_name_to_ids[input_clean]:
            resolved.append((iid, "Exact Name (master)"))

    if not resolved:
        sem_id, sem_score = semantic_search(raw)
        if sem_id:
            resolved.append((sem_id, f"Semantic Search (score={sem_score:.2f})"))

    if not resolved:
        match, score = process.extractOne(input_clean, master_name_to_ids.keys(), scorer=fuzz.token_sort_ratio)
        if score >= 55:
            for iid in master_name_to_ids[match]:
                resolved.append((iid, f"Fuzzy Name (master) (score={score})"))

    return resolved

# ----------------------------
# Forecasting function
# ----------------------------
def forecast_item(item_ids, periods: int = 7, method: str = "Unknown"):
    forecasts = []
    for iid in item_ids:
        cur.execute(
            "SELECT quantity_consumed FROM consumption WHERE inventory_id=%s ORDER BY date DESC LIMIT 7",
            (iid,)
        )
        rows = cur.fetchall()
        avg_consumption = np.mean([float(r[0] or 0) for r in rows]) if rows else 2.0

        cur.execute(
            "SELECT closing_stock, min_stock FROM inventory_master WHERE inventory_id=%s",
            (iid,)
        )
        row = cur.fetchone()
        available_stock = float(row[0]) if row and row[0] is not None else 100.0
        min_stock_limit = float(row[1]) if row and row[1] is not None else 10.0

        for day in range(periods):
            y_pred = avg_consumption * (1 + 0.05 * np.sin(day))
            stock_warning = (available_stock - y_pred) < min_stock_limit
            forecasts.append({
                "Date": (pd.Timestamp.today() + pd.Timedelta(days=day + 1)).strftime("%Y-%m-%d"),
                "Inventory_ID": iid,
                "Predicted_Consumption": round(y_pred, 2),
                "Available_Stock": round(available_stock, 2),
                "Stock_Warning": stock_warning,
                "Search_Method": method
            })
            available_stock = max(0.0, available_stock - y_pred)
    return forecasts

# ----------------------------
# Fetch inventory data
# ----------------------------
def fetch_inventory_data(item_ids):
    results = []
    for iid in item_ids:
        cur.execute("SELECT * FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        if not row:
            continue
        cols = [desc[0] for desc in cur.description]
        master_data = dict(zip(cols, row))

        cur.execute(
            "SELECT date, quantity_consumed FROM consumption WHERE inventory_id=%s ORDER BY date DESC LIMIT 7",
            (iid,)
        )
        last_consumption = [{"date": r[0], "quantity_consumed": float(r[1])} for r in cur.fetchall()]

        results.append({"Inventory_Master": master_data, "Consumption": last_consumption})
    return results

# ----------------------------
# Recommendation helper
# ----------------------------
def recommend_alternatives(item_name: str, top_k: int = 3):
    # Search all inventory items semantically
    if len(inventory_embeddings) == 0:
        return []
    query_emb = sem_model.encode(item_name)
    query_emb = np.array(query_emb, dtype=np.float32)
    emb_norms = np.linalg.norm(emb_matrix, axis=1) * np.linalg.norm(query_emb)
    sims = np.dot(emb_matrix, query_emb) / (emb_norms + 1e-10)

    top_indices = sims.argsort()[-top_k:][::-1]
    alternatives = []
    for idx in top_indices:
        iid = inventory_ids[idx]
        cur.execute("SELECT item_name FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        if row:
            alternatives.append(row[0])
    return alternatives

# ----------------------------
# MCP Tool: Check Stock with automatic recommendation
# ----------------------------
@mcp.tool
def check_stock(item_name: str):
    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    item_ids = [iid for iid, _ in resolved_list]
    data_list = fetch_inventory_data(item_ids)

    results = []
    for data in data_list:
        master = data["Inventory_Master"]
        closing_stock = float(master.get("closing_stock", 0))
        min_stock = float(master.get("min_stock", 10))
        stock_status = "Out of Stock" if closing_stock == 0 else ("Low Stock" if closing_stock < min_stock else "In Stock")

        predicted_7_days = forecast_item([master.get("inventory_id")], periods=7, method="Check Stock")

        entry = {
            "Inventory_ID": master.get("inventory_id"),
            "Item_Name": master.get("item_name"),
            "Closing_Stock": closing_stock,
            "Min_Stock_Limit": min_stock,
            "Stock_Status": stock_status,
            "Last_Consumption_7_Days": data.get("Consumption", []),
            "Predicted_Consumption_7_Days": predicted_7_days
        }

        if stock_status in ["Out of Stock", "Low Stock"]:
            entry["Alternatives"] = recommend_alternatives(master.get("item_name"))

        results.append(entry)

    results.sort(key=lambda x: (0 if x["Stock_Status"]=="Out of Stock" else (1 if x["Stock_Status"]=="Low Stock" else 2)))
    return results

# ----------------------------
# MCP Tool: Update Inventory after Purchase with alternative suggestion
# ----------------------------
@mcp.tool
def update_inventory_after_purchase(item_name: str, quantity_purchased: float):
    if not item_name or quantity_purchased <= 0:
        return {"error": "Invalid item or quantity"}

    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    iid = resolved_list[0][0]
    cur.execute(
        "SELECT closing_stock, min_stock FROM inventory_master WHERE inventory_id=%s", (iid,)
    )
    row = cur.fetchone()
    if not row:
        return {"error": f"No inventory record for ID {iid}"}

    current_stock = float(row[0])
    min_stock = float(row[1]) if row[1] is not None else 10.0

    new_stock = max(0.0, current_stock - quantity_purchased)

    result = {
        "Inventory_ID": iid,
        "Previous_Stock": current_stock,
        "Quantity_Purchased": quantity_purchased,
        "Updated_Stock": new_stock
    }

    # If purchase would cause low stock or out-of-stock
    if new_stock <= min_stock:
        result["Stock_Status"] = "Low Stock" if new_stock > 0 else "Out of Stock"
        result["Alternatives"] = recommend_alternatives(item_name)
        result["Message"] = (
            f"Requested quantity cannot be fully fulfilled. "
            f"Available stock: {current_stock}. Suggested alternatives provided."
        )
    else:
        # Update inventory normally
        cur.execute(
            "UPDATE inventory_master SET closing_stock=%s WHERE inventory_id=%s",
            (new_stock, iid)
        )
        conn.commit()
        result["Stock_Status"] = "In Stock"
        result["Message"] = f"Purchase recorded successfully. Updated stock: {new_stock}"

    return result

    if not item_name or quantity_purchased <= 0:
        return {"error": "Invalid item or quantity"}

    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    iid = resolved_list[0][0]
    cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
    row = cur.fetchone()
    if not row:
        return {"error": f"No inventory record for ID {iid}"}

    current_stock = float(row[0])
    new_stock = max(0.0, current_stock - quantity_purchased)

    cur.execute("UPDATE inventory_master SET closing_stock=%s WHERE inventory_id=%s", (new_stock, iid))
    conn.commit()

    result = {
        "Inventory_ID": iid,
        "Previous_Stock": current_stock,
        "Quantity_Purchased": quantity_purchased,
        "Updated_Stock": new_stock
    }

    # If after purchase stock is zero or low, recommend alternatives
    if new_stock <= 0 or new_stock < 10:
        result["Alternatives"] = recommend_alternatives(item_name)

    return result

# ----------------------------
# MCP Tool: Predict Demand
# ----------------------------
# ----------------------------
# MCP Tool: Predict Demand / Reorder Item
# ----------------------------
@mcp.tool
def reorder_item(item_name: str, quantity: int = 1):
    """
    Prepares a reorder request for the specified item without sending the email directly.
    Returns the details needed for an agent or external process to send the email.
    """
    try:
        if not item_name or quantity <= 0:
            return {"error": "Invalid item name or quantity"}

        resolved_list = resolve_inventory_ids(item_name)
        if not resolved_list:
            return {"error": f"Inventory '{item_name}' not found"}

        iid = resolved_list[0][0]

        cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        current_stock = float(row[0]) if row else 0.0

        # Compose email content for external sending
        subject = f"Reorder Request: {item_name}"
        body = f"Please reorder {quantity} units of {item_name}. Current stock: {current_stock}."

        return {
            "Inventory_ID": iid,
            "Item_Name": item_name,
            "Current_Stock": current_stock,
            "Reorder_Quantity": quantity,
            "Status": "Reorder Email Required",
            "Email_To_Send": {
                "recipient": "n.megha82@gmail.com",
                "subject": subject,
                "body": body
            }
        }

    except Exception as e:
        return {"error": f"Reorder failed: {str(e)}"}

    try:
        if not item_name or quantity <= 0:
            return {"error": "Invalid item name or quantity"}

        resolved_list = resolve_inventory_ids(item_name)
        if not resolved_list:
            return {"error": f"Inventory '{item_name}' not found"}

        iid = resolved_list[0][0]

        cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        current_stock = float(row[0]) if row else 0.0

        # Compose email
        subject = f"Reorder Request: {item_name}"
        body = f"Please reorder {quantity} units of {item_name}. Current stock: {current_stock}."

        # Send email using Gmail OAuth
        try:
            email_result = send_email_oauth("n.megha82@gmail.com", subject, body)
            status = "Reorder Email Sent" if email_result.get("status") == "success" else "Email Failed"
        except Exception as e:
            email_result = {"error": str(e)}
            status = "Email Failed"

        # Return info without logging to DB
        return {
            "Inventory_ID": iid,
            "Item_Name": item_name,
            "Current_Stock": current_stock,
            "Reorder_Quantity": quantity,
            "Status": status,
            "Email_Details": email_result
        }

    except Exception as e:
        return {"error": f"Reorder failed: {str(e)}"}

    try:
        if not item_name or quantity <= 0:
            return {"error": "Invalid item name or quantity"}

        resolved_list = resolve_inventory_ids(item_name)
        if not resolved_list:
            return {"error": f"Inventory '{item_name}' not found"}

        iid = resolved_list[0][0]

        cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        current_stock = float(row[0]) if row else 0.0

        # Compose reorder email
        subject = f"Reorder Request: {item_name}"
        body = f"Please reorder {quantity} units of {item_name}. Current stock: {current_stock}."

        # Call Gmail tool safely
        try:
            email_result = send_email("n.megha82@gmail.com", subject, body)
            status = "Reorder Email Sent" if email_result.get("status") == "success" else "Email Failed"
        except Exception as e:
            email_result = {"error": str(e)}
            status = "Email Failed"

        # Log reorder in DB (optional)
        cur.execute(
            "INSERT INTO reorder_log (inventory_id, quantity, status) VALUES (%s, %s, %s)",
            (iid, quantity, status)
        )
        conn.commit()

        return {
            "Inventory_ID": iid,
            "Item_Name": item_name,
            "Current_Stock": current_stock,
            "Reorder_Quantity": quantity,
            "Status": status,
            "Email_Details": email_result
        }

    except Exception as e:
        return {"error": f"Reorder failed: {str(e)}"}


@mcp.tool
def predict_demand(item_name: str):
    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    item_ids = [iid for iid, _ in resolved_list]
    forecasts = forecast_item(item_ids, periods=7)
    return forecasts



    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}
    iid = resolved_list[0][0]

    cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
    row = cur.fetchone()
    current_stock = float(row[0]) if row else 0

    subject = f"Reorder Request: {item_name}"
    body = f"Please reorder {quantity} units of {item_name}. Current stock: {current_stock}."

    # Instead of sending email, return the details for the agent to call send_email
    return {
        "Inventory_ID": iid,
        "Item_Name": item_name,
        "Current_Stock": current_stock,
        "Reorder_Quantity": quantity,
        "Status": "Reorder Email Required",
        "Email_To_Send": {
            "recipient": "n.megha82@gmail.com",
            "subject": subject,
            "body": body
        }
    }


    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    iid = resolved_list[0][0]

    cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
    row = cur.fetchone()
    current_stock = float(row[0]) if row else 0

    # Compose email content
    subject = f"Reorder Request: {item_name}"
    body = f"Please reorder {quantity} units of {item_name}. Current stock: {current_stock}."

    # Send email using Gmail OAuth tool
    email_result = send_email("n.megha82@gmail.com", subject, body)

    # Log reorder in DB (optional)
    cur.execute(
        "INSERT INTO reorder_log (inventory_id, quantity, status) VALUES (%s, %s, %s)",
        (iid, quantity, "Requested")
    )
    conn.commit()

    return {
        "Inventory_ID": iid,
        "Item_Name": item_name,
        "Current_Stock": current_stock,
        "Reorder_Quantity": quantity,
        "Status": "Reorder Email Sent" if email_result.get("status")=="success" else "Email Failed",
        "Email_Details": email_result
    }
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CLIENT_SECRET_FILE = "client_secret.json"  # <-- your Google credentials
TOKEN_FILE = "token.pickle"

def authenticate_gmail():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as t:
            creds = pickle.load(t)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as t:
            pickle.dump(creds, t)
    return creds

def send_email_oauth(recipient: str, subject: str, body: str):
    service = build("gmail", "v1", credentials=authenticate_gmail())
    msg = MIMEMultipart()
    msg["to"] = recipient
    msg["subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw_msg}).execute()
    return True

@mcp.tool
def send_email(recipient: str, subject: str, body: str):
    """
    Sends email notifications using Gmail OAuth authentication.
    
    This tool enables the agent to send alerts and reports via email. It uses OAuth2
    for secure Gmail authentication, requiring valid Google credentials setup.
    
    Prerequisites:
        - Google API credentials file (client_secret.json)
        - First-time authentication creates token.pickle for subsequent uses
        - Gmail API must be enabled in Google Cloud Console
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Email subject line
        body (str): Plain text email body content
    
    Returns:
        dict: Operation status containing:
            - status (str): Either "success", "failed", or "error"
            - message (str): Success message with recipient email
            - error (str, optional): Error description if operation failed
    
    Use Cases:
        - Alert when stock falls below minimum threshold
        - Send daily/weekly inventory reports
        - Notify about items requiring urgent restocking
        - Schedule demand forecast notifications
    
    Example:
        >>> send_email("manager@hospital.com", "Low Stock Alert", "Syringes stock critically low")
    """
    try:
        if not recipient or not subject or not body:
            return {"status": "error", "error": "Recipient, subject, or body missing"}
        
        # Send via Gmail OAuth
        ok = send_email_oauth(recipient, subject, body)
        if ok:
            return {"status": "success", "message": f"Email sent to {recipient}"}
        else:
            return {"status": "failed", "message": "Unknown failure"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@mcp.tool
def general_inventory_knowledge(query: str):
    """
    General knowledge tool for ANY inventory-related query.
    Automatically joins vendors, stock, thresholds, consumption, categories.
    """

    if not query:
        return {"error": "No query provided"}

    query_norm = normalize_text(query)
    results = []

    try:
        # 🟦 FULL JOIN: inventory + vendor + consumption
        sql = """
            SELECT 
                im.inventory_id,
                im.item_name,
                im.item_type,
                im.closing_stock,
                im.min_stock,
                v.vendor_id,
                v.vendor_name,
                v.contact_number,
                v.default_lead_time_days,
                c.date AS consumption_date,
                c.quantity_consumed
            FROM inventory_master im
            LEFT JOIN vendor_master v ON im.vendor_id = v.vendor_id
            LEFT JOIN consumption c ON im.inventory_id = c.inventory_id
        """

        cur.execute(sql)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]

        # 🟦 Simple matching logic
        for row in rows:
            record = {col: row[idx] for idx, col in enumerate(cols)}

            fields = [
                str(record.get("item_name", "")).lower(),
                str(record.get("vendor_name", "")).lower(),
                str(record.get("item_type", "")).lower()
            ]

            # Any keyword match → include
            if any(word in " ".join(fields) for word in query_norm.split()):
                results.append(record)

        # 🟦 Fallback: semantic search  
        if not results and inventory_embeddings:
            sem_id, score = semantic_search(query)
            if sem_id:
                cur.execute(
                    """
                    SELECT 
                        im.inventory_id,
                        im.item_name,
                        im.item_type,
                        im.closing_stock,
                        im.min_stock,
                        v.vendor_id,
                        v.vendor_name,
                        v.contact_number,
                        v.default_lead_time_days ,
                        c.date AS consumption_date,
                        c.quantity_consumed
                    FROM inventory_master im
                    LEFT JOIN vendor_master v ON im.vendor_id = v.vendor_id
                    LEFT JOIN consumption c ON im.inventory_id = c.inventory_id
                    WHERE im.inventory_id = %s
                    """,
                    (sem_id,)
                )
                row = cur.fetchone()
                if row:
                    record = dict(zip(cols, row))
                    record["match"] = f"semantic ({score:.2f})"
                    results.append(record)

        if not results:
            return {"message": "No relevant information found."}

        return {"query": query, "results": results}

    except psycopg2.Error as db_err:
        return {
            "error": "Database query failed",
            "details": str(db_err)
        }

    except Exception as e:
        return {
            "error": "Unexpected error",
            "details": str(e)
        }

    

# ----------------------------
# Run MCP Server
# ----------------------------
if __name__ == "__main__":
    print("🚀 Inventory & Demand MCP running on port 8000 (SSE enabled)")
    mcp.run(transport="sse", port=8000)

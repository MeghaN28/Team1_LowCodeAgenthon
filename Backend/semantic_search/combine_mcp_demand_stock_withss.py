# combined_mcp_demand_stock_clean.py
# ---------------------------------------
# MCP Agent: Inventory & Demand
# Features:
# - Multi-item inventory tracking
# - Stock check with real-time status
# - Forecasting 7-day consumption
# - Automatic alternative recommendations via embeddings
# - Update inventory after purchase
# - Reorder & email notifications
# ---------------------------------------

import os
import re
import pickle
import base64
import psycopg2
import pandas as pd
import numpy as np
from fastmcp import FastMCP
from thefuzz import fuzz, process
from sentence_transformers import SentenceTransformer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import io
import pdfplumber
from PIL import Image
import pytesseract
from datetime import datetime
import uuid
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
    dbname="medical_inventory_db",
    user="meghanarendrasimha",
    password="Welcome@123"
)
cur = conn.cursor()

# ----------------------------
# Utilities
# ----------------------------
def normalize_text(s: str):
    if not s: return ""
    s = str(s).replace('\xa0', ' ').lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

# ----------------------------
# Load inventory master
# ----------------------------
def load_inventory_master():
    cur.execute("SELECT inventory_id, item_name FROM inventory_master")
    rows = cur.fetchall()
    master_map = {}
    for iid, name in rows:
        if name:
            master_map.setdefault(normalize_text(name), []).append(str(iid))
    return master_map

master_name_to_ids = load_inventory_master()
inventory_ids_set = set(iid for ids in master_name_to_ids.values() for iid in ids)

# ----------------------------
# Semantic embeddings
# ----------------------------
sem_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 384-dim

def load_inventory_embeddings():
    cur.execute("SELECT inventory_id, embedding FROM inventory_master WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    emb_map = {}
    for iid, emb in rows:
        if emb:
            if isinstance(emb, str):
                emb = np.fromstring(emb.strip('[]'), sep=',', dtype=np.float32)
            emb_map[str(iid)] = np.array(emb, dtype=np.float32)
    return emb_map

inventory_embeddings = load_inventory_embeddings()
inventory_ids = list(inventory_embeddings.keys())
emb_matrix = np.stack(list(inventory_embeddings.values())) if inventory_embeddings else np.zeros((0,384), dtype=np.float32)

def semantic_search(query: str, top_k: int = 3, threshold: float = 0.6):
    if len(inventory_embeddings) == 0: return []
    query_emb = np.array(sem_model.encode(query), dtype=np.float32)
    sims = np.dot(emb_matrix, query_emb) / (np.linalg.norm(emb_matrix, axis=1) * np.linalg.norm(query_emb) + 1e-10)
    top_indices = np.argsort(sims)[-top_k:][::-1]
    return [(inventory_ids[i], sims[i]) for i in top_indices if sims[i] >= threshold]

# ----------------------------
# Resolve inventory IDs
# ----------------------------
def resolve_inventory_ids(input_str: str):
    resolved = []
    input_clean = normalize_text(input_str)
    if input_clean in master_name_to_ids:
        for iid in master_name_to_ids[input_clean]:
            resolved.append((iid, "Exact Name (master)"))
    if not resolved:
        sem_results = semantic_search(input_str)
        for iid, score in sem_results:
            resolved.append((iid, f"Semantic Search (score={score:.2f})"))
    if not resolved:
        match, score = process.extractOne(input_clean, master_name_to_ids.keys(), scorer=fuzz.token_sort_ratio)
        if score >= 55:
            for iid in master_name_to_ids[match]:
                resolved.append((iid, f"Fuzzy Name (master) (score={score})"))
    return resolved

# ----------------------------
# Fetch inventory data
# ----------------------------
def fetch_inventory_data(item_ids):
    results = []
    for iid in item_ids:
        cur.execute("SELECT * FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        if not row: continue
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
# Forecast consumption
# ----------------------------
def forecast_item(item_ids, periods: int = 7):
    forecasts = []
    today = pd.Timestamp.today().normalize()
    for iid in item_ids:
        # Fetch last 7 days including today
        cur.execute("""
            SELECT date, quantity_consumed 
            FROM consumption 
            WHERE inventory_id=%s AND date >= %s
            ORDER BY date ASC
        """, (iid, today - pd.Timedelta(days=6)))  # last 7 days including today
        rows = cur.fetchall()

        # Map date -> quantity for existing rows
        daily_consumption = {r[0]: float(r[1] or 0) for r in rows}
        avg_consumption = np.mean(list(daily_consumption.values())) if daily_consumption else 2.0

        cur.execute("SELECT closing_stock, min_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        available_stock = float(row[0]) if row and row[0] is not None else 100.0
        min_stock_limit = float(row[1]) if row and row[1] is not None else 10.0

        for day in range(periods):
            date = (today + pd.Timedelta(days=day)).date()
            consumed_today = daily_consumption.get(date, avg_consumption)
            y_pred = consumed_today * (1 + 0.05*np.sin(day))
            stock_warning = (available_stock - y_pred) < min_stock_limit
            forecasts.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Inventory_ID": iid,
                "Predicted_Consumption": round(y_pred, 2),
                "Available_Stock": round(available_stock,2),
                "Stock_Warning": stock_warning
            })
            available_stock = max(0.0, available_stock - y_pred)
    return forecasts

# ----------------------------
# Recommend alternatives
# ----------------------------
def recommend_alternatives(item_name: str, top_k: int = 3):
    seen = set()
    alternatives = []
    for iid, score in semantic_search(item_name, top_k=top_k):
        cur.execute("SELECT item_name, closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
        row = cur.fetchone()
        if row and row[1] > 0:
            name = row[0]
            if name not in seen:
                alternatives.append(name)
                seen.add(name)
    return alternatives

# ----------------------------
# MCP Tools
# ----------------------------

@mcp.tool
def check_stock(item_name: str):
    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list: return {"error": f"Inventory '{item_name}' not found"}
    item_ids = [iid for iid, _ in resolved_list]
    data_list = fetch_inventory_data(item_ids)

    results = []
    for data in data_list:
        master = data["Inventory_Master"]
        closing_stock = float(master.get("closing_stock",0))
        min_stock = float(master.get("min_stock",10))
        stock_status = "Out of Stock" if closing_stock==0 else ("Low Stock" if closing_stock < min_stock else "In Stock")

        entry = {
            "Inventory_ID": master.get("inventory_id"),
            "Item_Name": master.get("item_name"),
            "Closing_Stock": closing_stock,
            "Min_Stock_Limit": min_stock,
            "Stock_Status": stock_status,
            "Last_Consumption_7_Days": data.get("Consumption", []),
            "Predicted_Consumption_7_Days": forecast_item([master.get("inventory_id")])
        }

        if stock_status in ["Out of Stock", "Low Stock"]:
            entry["Alternatives"] = recommend_alternatives(master.get("item_name"))

        results.append(entry)

    results.sort(key=lambda x: (0 if x["Stock_Status"]=="Out of Stock" else (1 if x["Stock_Status"]=="Low Stock" else 2)))
    return results

@mcp.tool
def update_inventory_after_purchase(item_name: str, quantity_purchased: float):
    if quantity_purchased <= 0: return {"error": "Invalid quantity"}
    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list: return {"error": f"Inventory '{item_name}' not found"}

    iid = resolved_list[0][0]
    cur.execute("SELECT closing_stock, min_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
    row = cur.fetchone()
    if not row: return {"error": f"No inventory record for ID {iid}"}
    current_stock = float(row[0])
    min_stock = float(row[1] or 10)

    fulfilled_qty = min(quantity_purchased, current_stock)
    new_stock = max(0.0, current_stock - fulfilled_qty)

    cur.execute("UPDATE inventory_master SET closing_stock=%s WHERE inventory_id=%s", (new_stock, iid))
    conn.commit()

    stock_status = "In Stock" if new_stock > min_stock else ("Low Stock" if new_stock>0 else "Out of Stock")
    result = {
        "Inventory_ID": iid,
        "Item_Name": item_name,
        "Previous_Stock": current_stock,
        "Quantity_Purchased": fulfilled_qty,
        "Updated_Stock": new_stock,
        "Stock_Status": stock_status,
        "Message": f"Purchase recorded. Updated stock: {new_stock}"
    }

    if stock_status in ["Low Stock","Out of Stock"]:
        result["Alternatives"] = recommend_alternatives(item_name)

    return result

@mcp.tool
def predict_demand(item_name: str):
    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list: return {"error": f"Inventory '{item_name}' not found"}
    item_ids = [iid for iid,_ in resolved_list]
    return forecast_item(item_ids)


@mcp.tool
def reorder_item(item_name: str, reorder_quantity: int = 10):
    """
    MCP wrapper: Calls reusable reorder function.
    """
    return process_reorder(item_name, reorder_quantity)

def process_reorder(item_name: str, reorder_quantity: int = 10):
    """
    Core logic for reordering an item:
    - Resolve inventory ID
    - Get stock
    - Send email
    - Insert log
    Returns a result dict.
    """

    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    iid = resolved_list[0][0]

    # Fetch current stock
    cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
    row = cur.fetchone()
    current_stock = int(row[0]) if row and row[0] is not None else 0

    # Prepare email
    recipient = "n.megha82@gmail.com"
    subject = f"Reorder Alert: {item_name}"
    body = f"""
    Dear Inventory Manager,

    Please reorder the item: {item_name} (Inventory ID: {iid})
    Current Stock: {current_stock}
    Reorder Quantity: {reorder_quantity}

    This is an automated notification from the Inventory MCP system.
    """

    # Send email
    email_status = send_reorder_email(recipient, subject, body)

    # Insert into reorder_log
    cur.execute("""
        INSERT INTO reorder_log 
        (inventory_id, item_name, reorder_quantity, current_stock, status, email_recipient, email_subject, email_body)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (iid, item_name, reorder_quantity, current_stock, email_status, recipient, subject, body))
    
    conn.commit()

    return {
        "Inventory_ID": iid,
        "Item_Name": item_name,
        "Current_Stock": current_stock,
        "Reorder_Quantity": reorder_quantity,
        "Email_Status": email_status,
        "Message": "Reorder logged and email processed"
    }


# Folder path for receipts
def send_reorder_email(recipient: str, subject: str, body: str):
    """
    Sends an email using Gmail API OAuth2.
    Returns a status string.
    """

    # Prepare Gmail API MIME message
    message = MIMEMultipart()
    message['to'] = recipient
    message['subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        # Gmail API scopes
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']
        creds = None

        # Load saved OAuth credentials
        if os.path.exists('token.json'):
            with open('token.json', 'rb') as token_file:
                creds = pickle.load(token_file)

        # If expired / no token → re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret_2_573959129688-mef2hfbg4k6bu0b2e91to9s68681e4rs.apps.googleusercontent.com.json', 
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save refreshed token
            with open('token.json', 'wb') as token_file:
                pickle.dump(creds, token_file)

        # Build Gmail service and send email
        service = build('gmail', 'v1', credentials=creds)
        send_message = {'raw': raw_message}
        service.users().messages().send(userId='me', body=send_message).execute()

        return "Email Sent"

    except Exception as e:
        return f"Email Failed: {str(e)}"

@mcp.tool
def process_receipts_folder():
    """
    Processes receipts in ~/Documents/receipts, updates inventory_master and consumption table,
    and automatically triggers reorder if stock is low or 0.
    """
    RECEIPTS_FOLDER = os.path.expanduser("~/Documents/receipts")
    os.makedirs(RECEIPTS_FOLDER, exist_ok=True)

    today = datetime.today().date()
    all_results = []

    files = [f for f in os.listdir(RECEIPTS_FOLDER) if f.lower().endswith(('png','jpg','jpeg','pdf'))]

    for filename in files:
        file_path = os.path.join(RECEIPTS_FOLDER, filename)
        text = ""

        # -----------------------------
        # EXTRACT TEXT FROM FILE
        # -----------------------------
        try:
            if filename.lower().endswith(('png','jpg','jpeg')):
                img = Image.open(file_path)
                text = pytesseract.image_to_string(img)

            elif filename.lower().endswith('pdf'):
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

            else:
                all_results.append({"filename": filename, "error": "Unsupported file type"})
                continue

        except Exception as e:
            all_results.append({"filename": filename, "error": str(e)})
            continue


        # -----------------------------
        # PARSE ITEMS
        # -----------------------------
        items = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            match = re.match(r'(.+?)[\s:-]+(\d+)', line)
            if match:
                items.append({
                    "name": match.group(1).strip(),
                    "quantity": int(match.group(2))
                })

        if not items:
            all_results.append({"filename": filename, "error": "No items found"})
            continue


        receipt_results = []
        for item in items:
            name = item["name"]
            qty = item["quantity"]

            resolved_list = resolve_inventory_ids(name)
            if not resolved_list:
                receipt_results.append({"item": name, "quantity": qty, "status": "Item not found"})
                continue

            iid = resolved_list[0][0]

            # -----------------------------
            # CURRENT + MIN STOCK
            # -----------------------------
            cur.execute("SELECT closing_stock, min_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
            row = cur.fetchone()

            current_stock = float(row[0]) if row and row[0] is not None else 0
            min_stock = float(row[1] or 10)

            new_stock = max(0.0, current_stock - qty)

            # Update inventory_master
            cur.execute("UPDATE inventory_master SET closing_stock=%s WHERE inventory_id=%s",
                        (new_stock, iid))


            # -----------------------------
            # INSERT INTO consumption
            # -----------------------------
            transaction_id = str(uuid.uuid4())

            department = "General"
            staff_id = "SYSTEM"
            shift = "Morning"
            consumption_reason = "Purchase Receipt"
            batch_lot = None

            cur.execute(
                """
                INSERT INTO consumption
                (transaction_id, inventory_id, quantity_consumed, date,
                 department, staff_id, shift, consumption_reason, 
                 remaining_stock, batch_lot)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    transaction_id, iid, qty, today,
                    department, staff_id, shift, consumption_reason,
                    new_stock, batch_lot
                )
            )
            conn.commit()


            # -----------------------------
            # STOCK STATUS + AUTO-REORDER
            # -----------------------------
            stock_status = (
                "In Stock" if new_stock > min_stock
                else "Low Stock" if new_stock > 0
                else "Out of Stock"
            )

            reorder_triggered = None

            if stock_status in ("Low Stock", "Out of Stock"):
                reorder_triggered = process_reorder(name, reorder_quantity=10)


            receipt_results.append({
                "item": name,
                "quantity_consumed": qty,
                "Previous_Stock": current_stock,
                "Updated_Stock": new_stock,
                "Stock_Status": stock_status,
                "Reorder_Triggered": reorder_triggered
            })


        all_results.append({
            "filename": filename,
            "processed_items": receipt_results
        })


        # Delete processed file
        try:
            os.remove(file_path)
        except Exception as e:
            all_results.append({"filename": filename, "delete_error": str(e)})


    return {"success": True, "receipts_summary": all_results}

# ----------------------------
# Run MCP Server
# ----------------------------
if __name__=="__main__":
    print("🚀 Inventory & Demand MCP running on port 8000 (SSE enabled)")
    mcp.run(transport="sse", port=8000)

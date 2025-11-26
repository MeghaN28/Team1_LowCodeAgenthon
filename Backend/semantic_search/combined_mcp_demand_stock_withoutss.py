# combined_mcp_demand_stock.py
# ---------------------------------------
# MCP Agent for Inventory Data + Demand Forecast + Dashboard Report
# Handles multiple inventory IDs per item, stock warnings, and low-stock prioritization
# ---------------------------------------

import base64
import pickle
import psycopg2
import pandas as pd
import numpy as np
from fastmcp import FastMCP
from thefuzz import fuzz, process
import re
from sentence_transformers import SentenceTransformer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

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
        master_map.setdefault(name, []).append(inv_id)  # store multiple IDs per item
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

# Precompute clean names
master_name_to_ids = {normalize_text(k): v for k, v in inventory_master_map.items()}
inventory_ids_set = set([iid for ids in inventory_master_map.values() for iid in ids])

# ----------------------------
# Semantic search setup
# ----------------------------
sem_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 128-dim

def load_inventory_embeddings():
    cur.execute("SELECT inventory_id, embedding FROM inventory_master WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    emb_map = {}
    for inv_id, emb in rows:
        if emb:
            emb_map[str(inv_id)] = np.array(emb, dtype=np.float32)
    return emb_map

inventory_embeddings = load_inventory_embeddings()
inventory_ids = list(inventory_embeddings.keys())
emb_matrix = np.stack(list(inventory_embeddings.values())) if inventory_embeddings else np.zeros((0,128))

def semantic_search(query: str, top_k: int = 1, threshold: float = 0.7):
    if len(inventory_embeddings) == 0:
        return None, 0.0
    query_emb = sem_model.encode(query)
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

    # Exact inventory_id match
    if input_upper in inventory_ids_set:
        resolved.append((input_upper, "Exact Inventory_ID"))

    # Exact name match
    if input_clean in master_name_to_ids:
        for iid in master_name_to_ids[input_clean]:
            resolved.append((iid, "Exact Name (master)"))

    # Semantic search
    if not resolved:
        sem_id, sem_score = semantic_search(raw)
        if sem_id:
            resolved.append((sem_id, f"Semantic Search (score={sem_score:.2f})"))

    # Fuzzy match
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
        # Last 7 days consumption
        cur.execute(
            "SELECT quantity_consumed FROM consumption WHERE inventory_id=%s ORDER BY date DESC LIMIT 7",
            (iid,)
        )
        rows = cur.fetchall()
        avg_consumption = np.mean([float(r[0] or 0) for r in rows]) if rows else 2.0

        # Current stock and min stock
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
# MCP Tool: Check Stock
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

        results.append({
            "Inventory_ID": master.get("inventory_id"),
            "Item_Name": master.get("item_name"),
            "Closing_Stock": closing_stock,
            "Min_Stock_Limit": min_stock,
            "Stock_Status": stock_status,
            "Last_Consumption_7_Days": data.get("Consumption", []),
            "Predicted_Consumption_7_Days": predicted_7_days
        })

    # Sort so Out of Stock and Low Stock come first
    results.sort(key=lambda x: (0 if x["Stock_Status"]=="Out of Stock" else (1 if x["Stock_Status"]=="Low Stock" else 2)))
    return results

# ----------------------------
# MCP Tool: Update Inventory after Purchase
# ----------------------------
@mcp.tool
def update_inventory_after_purchase(item_name: str, quantity_purchased: float):
    if not item_name or quantity_purchased <= 0:
        return {"error": "Invalid item or quantity"}

    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    iid = resolved_list[0][0]  # take first ID for update

    cur.execute("SELECT closing_stock FROM inventory_master WHERE inventory_id=%s", (iid,))
    row = cur.fetchone()
    if not row:
        return {"error": f"No inventory record for ID {iid}"}

    current_stock = float(row[0])
    new_stock = max(0.0, current_stock - quantity_purchased)

    cur.execute("UPDATE inventory_master SET closing_stock=%s WHERE inventory_id=%s", (new_stock, iid))
    conn.commit()

    return {
        "Inventory_ID": iid,
        "Previous_Stock": current_stock,
        "Quantity_Purchased": quantity_purchased,
        "Updated_Stock": new_stock
    }

# ----------------------------
# MCP Tool: Predict Demand
# ----------------------------
@mcp.tool
def predict_demand(item_name: str):
    resolved_list = resolve_inventory_ids(item_name)
    if not resolved_list:
        return {"error": f"Inventory '{item_name}' not found"}

    item_ids = [iid for iid, _ in resolved_list]
    forecasts = forecast_item(item_ids, periods=7)
    return forecasts

# ----------------------------
# Run MCP Server
# ----------------------------
if __name__ == "__main__":
    print("🚀 Inventory & Demand MCP running on port 8000 (SSE enabled)")
    mcp.run(transport="sse", port=8000)

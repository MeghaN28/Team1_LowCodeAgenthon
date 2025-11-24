# combined_inventory_demand_mcp_semantic.py
# ---------------------------------------
# MCP Agent for Inventory Data + Demand Forecast + Dashboard Report
# Semantic search (128-dim embeddings) for inventory name resolution
# Demand forecast now directly fetched from DB (no XGBoost)
# Corrected check_stock logic
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
    dbname="vectordb",
    user="meghanarendrasimha",
    password="Welcome@123"
)
cur = conn.cursor()

# ----------------------------
# Load historical dataset for inventory names mapping
# ----------------------------
historical_df = pd.read_csv("models/demand_forecast_base.csv", parse_dates=['Date'])
historical_df['Inventory_ID'] = historical_df['Inventory_ID'].astype(str)

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
        master_map[name] = inv_id
    return master_map

inventory_master_map = load_inventory_master_names()

# ----------------------------
# Normalization utilities and precompute cleaned name maps
# ----------------------------
def normalize_text(s: str):
    if not s:
        return ""
    s = str(s).replace('\xa0', ' ').lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

historical_names_clean = [normalize_text(n) for n in historical_df['Item_Name'].fillna("").astype(str)]
historical_name_to_id = dict(zip(historical_names_clean, historical_df['Inventory_ID'].astype(str)))

master_names_clean = [normalize_text(n) for n in inventory_master_map.keys()]
master_name_to_id = {normalize_text(k): v for k, v in inventory_master_map.items()}

combined_names_clean = list(master_name_to_id.keys()) + [n for n in historical_name_to_id if n not in master_name_to_id]
combined_name_to_id = {**master_name_to_id, **historical_name_to_id}

inventory_ids_set = set(historical_df['Inventory_ID'].astype(str)).union(set(master_name_to_id.values()))

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
# Utility functions
# ----------------------------
def extract_periods_from_query(query: str, default: int = 7) -> int:
    match = re.search(r'(\d+)\s*(day|days|week|weeks)', query.lower())
    if match:
        num = int(match.group(1))
        if "week" in match.group(2):
            num *= 7
        return num
    return default

def resolve_inventory_ids(input_str: str):
    if not input_str:
        return []

    raw = str(input_str).strip()
    input_upper = raw.upper()
    input_clean = normalize_text(raw)

    if input_upper in inventory_ids_set:
        return [(input_upper, "Exact Inventory_ID")]
    if input_clean in historical_name_to_id:
        return [(historical_name_to_id[input_clean], "Exact Name (historical)")]
    if input_clean in master_name_to_id:
        return [(master_name_to_id[input_clean], "Exact Name (master)")]

    sem_id, sem_score = semantic_search(raw)
    if sem_id:
        return [(sem_id, f"Semantic Search (score={sem_score:.2f})")]

    match = process.extractOne(input_clean, combined_names_clean, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= 55:
        inv_id = combined_name_to_id[match[0]]
        source = "Fuzzy Name (master)" if match[0] in master_name_to_id else "Fuzzy Name (historical)"
        return [(inv_id, f"{source} (score={match[1]})")]

    return []

# ----------------------------
# Forecasting functions (DB-driven)
# ----------------------------
def forecast_item(item_id: str, periods: int = 7, method: str = "Unknown"):
    cur.execute("SELECT avg_daily_consumption, initial_stock, minimum_required FROM inventory_master WHERE inventory_id=%s", (item_id,))
    row = cur.fetchone()
    avg_consumption = float(row[0]) if row and row[0] is not None else 2.0
    available_stock = float(row[1]) if row and row[1] is not None else 100.0
    min_stock_limit = float(row[2]) if row and row[2] is not None else 10.0

    forecasts = []
    for day in range(periods):
        y_pred = avg_consumption * (1 + 0.05 * np.sin(day))
        stock_warning = (available_stock - y_pred) < min_stock_limit
        forecasts.append({
            "Date": (pd.Timestamp.today() + pd.Timedelta(days=day + 1)).strftime("%Y-%m-%d"),
            "Inventory_ID": item_id,
            "Predicted_Consumption": round(y_pred, 2),
            "Available_Stock": round(available_stock, 2),
            "Stock_Warning": stock_warning,
            "Search_Method": method
        })
        available_stock = max(0.0, available_stock - y_pred)
    return forecasts

# ----------------------------
# Fetch inventory related data
# ----------------------------
def fetch_inventory_data(inventory_id: str):
    cur.execute("SELECT * FROM inventory_master WHERE inventory_id=%s", (inventory_id,))
    master_row = cur.fetchone()
    if not master_row:
        return {"error": f"No master data found for inventory ID {inventory_id}"}
    master_cols = [desc[0] for desc in cur.description]
    master_data = dict(zip(master_cols, master_row))

    cur.execute("SELECT date, quantity_consumed FROM consumption WHERE inventory_id=%s ORDER BY date DESC LIMIT 7", (inventory_id,))
    last_consumption = [{"date": r[0], "quantity_consumed": float(r[1])} for r in cur.fetchall()]

    return {"Inventory_Master": master_data, "Consumption": last_consumption}

# ----------------------------
# MCP Tools
# ----------------------------
@mcp.tool
def predict_demand(inventory_id_or_name: str):
    periods = extract_periods_from_query(inventory_id_or_name, default=7)
    resolved_list = resolve_inventory_ids(inventory_id_or_name)
    if not resolved_list:
        return [{
            "Inventory_ID": inventory_id_or_name,
            "Date": None,
            "Predicted_Consumption": 0,
            "Available_Stock": 0,
            "Stock_Warning": True,
            "Search_Method": "Not Found",
            "error": f"Inventory '{inventory_id_or_name}' not found"
        }]
    forecasts = []
    for inv_id, method in resolved_list:
        forecasts.extend(forecast_item(inv_id, periods, method))
    return forecasts

@mcp.tool
def check_stock(inventory_id_or_name: str):
    if not inventory_id_or_name:
        return {"Inventory_ID": None, "Item_Name": None, "Closing_Stock": 0.0, "Min_Stock_Limit": 0.0,
                "Stock_Warning": True, "Search_Method": "Not Provided", "Last_Consumption_7_Days": [],
                "Predicted_Consumption_7_Days": []}

    resolved_list = resolve_inventory_ids(inventory_id_or_name)
    if not resolved_list:
        return {"Inventory_ID": inventory_id_or_name, "Item_Name": None, "Closing_Stock": 0.0,
                "Min_Stock_Limit": 0.0, "Stock_Warning": True, "Search_Method": "Not Found",
                "Last_Consumption_7_Days": [], "Predicted_Consumption_7_Days": [],
                "error": f"Inventory '{inventory_id_or_name}' not found"}

    inv_id, method = resolved_list[0]
    data = fetch_inventory_data(inv_id)
    if "error" in data:
        return {"Inventory_ID": inv_id, "Item_Name": None, "Closing_Stock": 0.0, "Min_Stock_Limit": 0.0,
                "Stock_Warning": True, "Search_Method": method, "Last_Consumption_7_Days": [],
                "Predicted_Consumption_7_Days": [], "error": data["error"]}

    master = data["Inventory_Master"]
    closing_stock = float(master.get("initial_stock", 0))
    min_stock_limit = float(master.get("minimum_required", 10))
    stock_warning = closing_stock < min_stock_limit
    last_consumption = data.get("Consumption", [])
    predicted_7_days = forecast_item(inv_id, periods=7, method=method)

    return {
        "Inventory_ID": inv_id,
        "Item_Name": master.get("item_name"),
        "Closing_Stock": closing_stock,
        "Min_Stock_Limit": min_stock_limit,
        "Stock_Warning": stock_warning,
        "Search_Method": method,
        "Last_Consumption_7_Days": last_consumption,
        "Predicted_Consumption_7_Days": predicted_7_days
    }

# ----------------------------
# Gmail OAuth Send Email Tool
# ----------------------------
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CLIENT_SECRET_FILE = "client_secret.json"
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
    try:
        if not recipient or not subject or not body:
            return {"status": "error", "error": "Recipient, subject, or body missing"}
        ok = send_email_oauth(recipient, subject, body)
        if ok:
            return {"status": "success", "message": f"Email sent to {recipient}"}
        else:
            return {"status": "failed", "message": "Unknown failure"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# ----------------------------
# MCP Server Run
# ----------------------------
if __name__ == "__main__":
    print("🚀 Inventory & Demand MCP running on port 8000 (SSE enabled)")
    mcp.run(transport="sse", port=8000)

# demand_forecast_mcp_v9.py
# ---------------------------------------
# MCP Agent for Demand Forecasting using XGBoost + Fuzzy & Semantic Search
# Optimized with FAISS + Query Embedding Cache + Safe Matching
# ---------------------------------------

from fastmcp import FastMCP
from xgboost import XGBRegressor
import pandas as pd
from thefuzz import fuzz, process
from sentence_transformers import SentenceTransformer
import psycopg2
import re
import numpy as np
import faiss

# ----------------------------
# Initialize MCP
# ----------------------------
mcp = FastMCP("Demand Forecast Agent 🧠")

# ----------------------------
# Load trained XGBoost model
# ----------------------------
model_path = "models/demand_agent_xgb.json"
xgb_model = XGBRegressor()
xgb_model.load_model(model_path)

# ----------------------------
# Load historical dataset
# ----------------------------
historical_df = pd.read_csv("models/demand_forecast_base.csv", parse_dates=['Date'])
item_name_list = historical_df['Item_Name'].dropna().str.lower().unique().tolist()

# ----------------------------
# PostgreSQL Vector DB setup (for semantic search)
# ----------------------------

conn = psycopg2.connect(

)
cur = conn.cursor()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# ----------------------------
# Preload all item embeddings into FAISS
# ----------------------------
cur.execute("SELECT inventory_id, item_name, embedding FROM inventory_master")
inventory_data = cur.fetchall()

inventory_embeddings = []
inventory_ids = []
inventory_names = []

for inv_id, name, emb in inventory_data:
    inventory_ids.append(inv_id)
    inventory_names.append(name)
    if isinstance(emb, str):
        emb = np.array([float(x) for x in emb.strip('[]').split(',')])
    inventory_embeddings.append(emb.astype('float32'))

inventory_embeddings = np.vstack(inventory_embeddings)
faiss.normalize_L2(inventory_embeddings)

d = inventory_embeddings.shape[1]
faiss_index = faiss.IndexFlatIP(d)
faiss_index.add(inventory_embeddings)

# ----------------------------
# Query cache
# ----------------------------
query_cache = {}  # input_str -> (inventory_id, similarity)

# ----------------------------
# Extract periods from user query
# ----------------------------
def extract_periods_from_query(query: str, default: int = 7) -> int:
    match = re.search(r'(\d+)\s*(day|days|week|weeks)', query.lower())
    if match:
        num = int(match.group(1))
        if "week" in match.group(2):
            num *= 7
        return num
    return default

# ----------------------------
# Resolve inventory IDs safely
# ----------------------------

    """
    Resolve input string to one or more Inventory IDs.
    Returns: List of (Inventory_ID, Search_Method) tuples
    """
    input_lower = input_str.lower().strip()
    resolved = []

    try:
        # 1️⃣ Exact ID match
        if input_str in historical_df['Inventory_ID'].values:
            resolved.append((input_str, "Exact"))
            return resolved

        # 2️⃣ Fuzzy match
        best_match, score = process.extractOne(input_lower, item_name_list, scorer=fuzz.token_sort_ratio)
        if score is not None and score >= 85:
            matched_rows = historical_df[historical_df['Item_Name'].str.lower() == best_match]
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Fuzzy"))
            return resolved
        else:
            print(f"[DEBUG] Fuzzy match too weak ({score}) for '{input_str}' → skip")

        # 3️⃣ Substring match
        matched_rows = historical_df['Item_Name'].str.lower().str.contains(input_lower, na=False)
        matched_rows = historical_df[matched_rows]
        if not matched_rows.empty:
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Substring"))
            return resolved

        # 4️⃣ Semantic search with FAISS
        if input_str in query_cache:
            inv_id, sim = query_cache[input_str]
            if sim >= 0.7:
                resolved.append((inv_id, "Semantic (cached)"))
                return resolved
            else:
                print(f"[DEBUG] Cached semantic sim {sim:.2f} too low for '{input_str}'")

        query_emb = embedding_model.encode(input_str).astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_emb)
        D, I = faiss_index.search(query_emb, 1)
        similarity = float(D[0][0])
        if similarity < 0.7:
            print(f"[DEBUG] No good semantic match for '{input_str}' (sim={similarity:.2f})")
            return []

        inventory_id = inventory_ids[I[0][0]]
        query_cache[input_str] = (inventory_id, similarity)
        resolved.append((inventory_id, "Semantic"))
        return resolved

    except Exception as e:
        print(f"[resolve_inventory_ids error] {str(e)}")
        return []

    """
    Resolve input string to one or more Inventory IDs.
    Returns: List of (Inventory_ID, Search_Method) tuples
    """
    try:
        input_lower = input_str.lower().strip()
        resolved = []

        # 1️⃣ Exact ID match
        if input_str in historical_df['Inventory_ID'].values:
            resolved.append((input_str, "Exact"))
            return resolved

        # 2️⃣ Fuzzy match (only accept very strong ones)
        best_match, score = process.extractOne(input_lower, item_name_list, scorer=fuzz.token_sort_ratio)
        if score is not None and score >= 85:
            matched_rows = historical_df[historical_df['Item_Name'].str.lower() == best_match]
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Fuzzy"))
            return resolved
        else:
            print(f"[DEBUG] Fuzzy match too weak ({score}) for '{input_str}' → skip")

        # 3️⃣ Substring match
        matched_rows = historical_df[historical_df['Item_Name'].str.lower().str.contains(input_lower, na=False)]
        if not matched_rows.empty:
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Substring"))
            return resolved

        # 4️⃣ Semantic search with threshold
        if input_str in query_cache:
            inv_id, sim = query_cache[input_str]
            if sim >= 0.7:
                resolved.append((inv_id, "Semantic (cached)"))
                return resolved
            else:
                print(f"[DEBUG] Cached semantic sim {sim:.2f} too low for '{input_str}'")

        # Compute new embedding
        query_emb = embedding_model.encode(input_str).astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_emb)
        D, I = faiss_index.search(query_emb, 1)
        similarity = float(D[0][0])
        if similarity < 0.7:
            print(f"[DEBUG] No good semantic match for '{input_str}' (sim={similarity:.2f})")
            return []

        inventory_id = inventory_ids[I[0][0]]
        query_cache[input_str] = (inventory_id, similarity)
        resolved.append((inventory_id, "Semantic"))
        return resolved

    except Exception as e:
        print(f"[resolve_inventory_ids error] {str(e)}")
        return []

    try:
        input_lower = input_str.lower()
        resolved = []

        # 1️⃣ Exact ID match
        if input_str in historical_df['Inventory_ID'].values:
            resolved.append((input_str, "Exact"))
            return resolved

        # 2️⃣ Fuzzy match
        best_match, score = process.extractOne(input_lower, item_name_list, scorer=fuzz.token_sort_ratio)
        if score >= 85:
            matched_rows = historical_df[historical_df['Item_Name'].str.lower() == best_match]
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Fuzzy"))
            return resolved

        # 3️⃣ Substring match
        matched_rows = historical_df[historical_df['Item_Name'].str.lower().str.contains(input_lower)]
        if not matched_rows.empty:
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Substring"))
            return resolved

        # 4️⃣ Semantic search with threshold
        if input_str in query_cache:
            cached_id, sim = query_cache[input_str]
            if sim >= 0.7:
                resolved.append((cached_id, "Semantic"))
                return resolved

        query_emb = embedding_model.encode(input_str).astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_emb)
        D, I = faiss_index.search(query_emb, 1)
        similarity = float(D[0][0])
        best_idx = I[0][0]

        if similarity < 0.7:
            print(f"[DEBUG] No good semantic match for '{input_str}' (similarity={similarity:.2f})")
            return []

        inventory_id = inventory_ids[best_idx]
        query_cache[input_str] = (inventory_id, similarity)
        resolved.append((inventory_id, "Semantic"))
        return resolved

    except Exception as e:
        print(f"[resolve_inventory_ids error] {str(e)}")
        return []
def resolve_inventory_ids(input_str: str):
    """
    Resolve input string to one or more Inventory IDs.
    Returns: List of (Inventory_ID, Search_Method) tuples.
    Logic order:
        1. Exact Inventory_ID match
        2. Fuzzy match on Item_Name (score >= 85)
        3. Substring match on Item_Name
        4. Semantic search with FAISS (cosine similarity >= 0.7)
    """
    input_lower = input_str.lower().strip()
    resolved = []

    try:
        # -----------------------
        # 1️⃣ Exact match on Inventory_ID
        # -----------------------
        if input_str in historical_df['Inventory_ID'].values:
            resolved.append((input_str, "Exact"))
            return resolved

        # -----------------------
        # 2️⃣ Fuzzy match on Item_Name
        # -----------------------
        best_match, score = process.extractOne(input_lower, item_name_list, scorer=fuzz.token_sort_ratio)
        if score is not None and score >= 85:
            matched_rows = historical_df[historical_df['Item_Name'].str.lower() == best_match]
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Fuzzy"))
            return resolved
        else:
            print(f"[DEBUG] Fuzzy match too weak ({score}) for '{input_str}' → skip")

        # -----------------------
        # 3️⃣ Substring match on Item_Name
        # -----------------------
        matched_rows = historical_df[historical_df['Item_Name'].str.lower().str.contains(input_lower, na=False)]
        if not matched_rows.empty:
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Substring"))
            return resolved

        # -----------------------
        # 4️⃣ Semantic search with FAISS
        # -----------------------
        # Check cache first
        if input_str in query_cache:
            inv_id, sim = query_cache[input_str]
            if sim >= 0.7:
                resolved.append((inv_id, "Semantic (cached)"))
                return resolved
            else:
                print(f"[DEBUG] Cached semantic similarity {sim:.2f} too low → skip")

        # Compute embedding and search FAISS
        query_emb = embedding_model.encode(input_str).astype('float32').reshape(1, -1)
        faiss.normalize_L2(query_emb)
        D, I = faiss_index.search(query_emb, 1)
        similarity = float(D[0][0])
        if similarity < 0.7:
            print(f"[DEBUG] No semantic match for '{input_str}' (sim={similarity:.2f})")
            return []  # no match found

        # Good semantic match
        inventory_id = inventory_ids[I[0][0]]
        query_cache[input_str] = (inventory_id, similarity)
        resolved.append((inventory_id, "Semantic"))
        return resolved

    except Exception as e:
        print(f"[resolve_inventory_ids error] {str(e)}")
        return []

# ----------------------------
# Forecast function
# ----------------------------
def forecast_item(item_id: str, periods: int = 7, method: str = "Unknown"):
    df_item = historical_df[historical_df['Inventory_ID'] == item_id].sort_values('Date').copy()
    if df_item.empty:
        print(f"[DEBUG] No historical data for {item_id}")
        return [{
            "error": f"No historical data found for Inventory_ID '{item_id}'.",
            "Search_Method": method
        }]

    last_row = df_item.iloc[-1].copy()
    defaults = {
        'Closing_Stock': 100,
        'Lead_Time_Days': 3,
        'lead_time_days': 3,
        'min_stock_limit': 10,
        'max_capacity': 500,
        'Quantity_Consumed': 0
    }
    for col, val in defaults.items():
        if col not in last_row or pd.isna(last_row[col]):
            last_row[col] = val

    preds = []
    available_stock = last_row['Closing_Stock']
    min_stock_limit = float(last_row.get('min_stock_limit', 10))

    for day in range(periods):
        feat = {
            'Opening_Stock': float(available_stock),
            'Closing_Stock': float(available_stock),
            'Quantity_Restocked': 0.0,
            'Lead_Time_Days': float(last_row.get('Lead_Time_Days', 3)),
            'lead_time_days': float(last_row.get('lead_time_days', 3)),
            'min_stock_limit': min_stock_limit,
            'max_capacity': float(last_row.get('max_capacity', 500)),
            'day_of_week': int((last_row['Date'].dayofweek + 1) % 7),
            'month': int((last_row['Date'].month % 12) + 1)
        }

        # Lag features
        for lag in range(1, 8):
            feat[f'lag_{lag}'] = float(last_row['Quantity_Consumed'] if lag == 1 else last_row.get(f'lag_{lag-1}', 0))

        X_pred = pd.DataFrame([feat])
        y_pred = float(max(0, xgb_model.predict(X_pred)[0]))

        stock_warning = (available_stock - y_pred) < min_stock_limit

        preds.append({
            'Date': (last_row['Date'] + pd.Timedelta(days=day + 1)).strftime("%Y-%m-%d"),
            'Inventory_ID': str(item_id),
            'Predicted_Consumption': y_pred,
            'Available_Stock': float(available_stock),
            'Stock_Warning': stock_warning,
            'Search_Method': method
        })

        # Update for next day
        for lag in range(7, 1, -1):
            last_row[f'lag_{lag}'] = last_row.get(f'lag_{lag-1}', 0.0)
        last_row['lag_1'] = y_pred
        available_stock = max(0.0, available_stock - y_pred)
        last_row['Closing_Stock'] = available_stock

    return preds

# ----------------------------
# MCP Tool
# ----------------------------
@mcp.tool
def predict_demand(Input: str):
    try:
        periods = extract_periods_from_query(Input, default=7)
        resolved_list = resolve_inventory_ids(Input)

        if not resolved_list:
            return [{
                "error": f"Sorry, I could not find any inventory item matching '{Input}'. "
                         f"Please provide a valid product name or Inventory ID."
            }]

        all_forecasts = []
        for inv_id, method in resolved_list:
            forecast = forecast_item(inv_id, periods, method)
            all_forecasts.extend(forecast)

        return all_forecasts

    except Exception as e:
        return [{"error": f"Internal error: {str(e)}"}]

# ----------------------------
# Run MCP
# ----------------------------
if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)

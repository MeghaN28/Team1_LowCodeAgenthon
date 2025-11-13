# demand_forecast_mcp_v6.py
# ---------------------------------------
# MCP Agent for Demand Forecasting using XGBoost + Fuzzy & Semantic Search
# Supports user-defined forecast periods and realistic stock warnings
# ---------------------------------------

from fastmcp import FastMCP
from xgboost import XGBRegressor
import pandas as pd
from thefuzz import fuzz, process
from sentence_transformers import SentenceTransformer
import psycopg2
import re

# ----------------------------
# Initialize MCP
# ----------------------------
mcp = FastMCP("Demand Forecast Agent 🧠")

# ----------------------------
# Load trained XGBoost model (JSON)
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
    host="",
    port="",
    dbname="",
    user="",
    password=""
)
cur = conn.cursor()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim embeddings

# ----------------------------
# Optional category map for generic queries
# ----------------------------
CATEGORY_MAP = {
    "amoxicillin capsules": ["INV00001"],
    "painkillers": ["INV00003", "INV00004"],
    "statins": ["INV00005", "INV00009"],
    "blood pressure medicine": ["INV00006", "INV00010"],
    "nitrile gloves": ["INV00001"]
}

# ----------------------------
# Extract periods from user query
# ----------------------------
def extract_periods_from_query(query: str, default: int = 7) -> int:
    """
    Extract number of days from user query, e.g., "for 10 days" → 10
    Supports weeks -> converts to days
    """
    match = re.search(r'(\d+)\s*(day|days|week|weeks)', query.lower())
    if match:
        num = int(match.group(1))
        if "week" in match.group(2):
            num *= 7
        return num
    return default

# ----------------------------
# Resolve Inventory_ID(s)
# ----------------------------
def resolve_inventory_ids(input_str: str):
    """
    Resolve input string to one or more Inventory IDs.
    Returns: List of (Inventory_ID, Search_Method) tuples
    """
    try:
        input_lower = input_str.lower()
        resolved = []

        # 0️⃣ Category map fallback
        for cat, inv_list in CATEGORY_MAP.items():
            if cat in input_lower:
                return [(inv_id, "CategoryMap") for inv_id in inv_list]

        # 1️⃣ Exact match on Inventory_ID
        if input_str in historical_df['Inventory_ID'].values:
            resolved.append((input_str, "Exact"))
            return resolved

        # 2️⃣ Fuzzy match on Item_Name
        best_match, score = process.extractOne(input_lower, item_name_list, scorer=fuzz.token_sort_ratio)
        if score >= 80:
            matched_rows = historical_df[historical_df['Item_Name'].str.lower() == best_match]
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Fuzzy"))
            return resolved

        # 3️⃣ Category-level match (contains keyword)
        matched_rows = historical_df[historical_df['Item_Name'].str.lower().str.contains(input_lower)]
        if not matched_rows.empty:
            for _, row in matched_rows.iterrows():
                resolved.append((row['Inventory_ID'], "Category"))
            return resolved

        # 4️⃣ Semantic search via vector DB
        query_embedding = embedding_model.encode(input_str).tolist()
        embedding_str = "[" + ",".join([str(x) for x in query_embedding]) + "]"
        sql = f"""
            SELECT inventory_id, item_name
            FROM inventory_master
            ORDER BY embedding <-> '{embedding_str}'::vector
            LIMIT 1
        """
        cur.execute(sql)
        result = cur.fetchone()
        if result:
            inventory_id, item_name = result
            resolved.append((inventory_id, "Semantic"))
            return resolved

        # 5️⃣ Nothing found
        return []

    except Exception as e:
        print(f"[resolve_inventory_ids error] {str(e)}")
        return []

# ----------------------------
# Forecast function with realistic stock warning
# ----------------------------
def forecast_item(item_id: str, periods: int = 7, method: str = "Unknown"):
    df_item = historical_df[historical_df['Inventory_ID'] == item_id].sort_values('Date').copy()
    if df_item.empty:
        return [{"error": f"No historical data found for Inventory_ID '{item_id}'.", "Search_Method": method}]

    last_row = df_item.iloc[-1].copy()
    # Default fallback values
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

        # ✅ Stock warning logic: warn if available stock falls below min_stock_limit
        stock_warning = (available_stock - y_pred) < min_stock_limit

        preds.append({
            'Date': (last_row['Date'] + pd.Timedelta(days=day + 1)).strftime("%Y-%m-%d"),
            'Inventory_ID': str(item_id),
            'Predicted_Consumption': y_pred,
            'Available_Stock': float(available_stock),
            'Stock_Warning': stock_warning,
            'Search_Method': method
        })

        # Update lag features and available stock for next day
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
        # Extract periods from user query
        periods = extract_periods_from_query(Input, default=7)

        resolved_list = resolve_inventory_ids(Input)

        if not resolved_list:
            return [{
                "error": f"Sorry, I could not find any inventory item matching '{Input}'. "
                         f"Please provide a valid product name or Inventory ID."
            }]

        all_forecasts = []
        for inv_id, method in resolved_list:
            try:
                forecast = forecast_item(inv_id, periods, method)
                all_forecasts.extend(forecast)
            except Exception as fe:
                all_forecasts.append({
                    "Inventory_ID": inv_id,
                    "error": f"Forecast failed: {str(fe)}",
                    "Search_Method": method
                })

        return all_forecasts

    except Exception as e:
        return [{"error": f"Internal error: {str(e)}"}]

# ----------------------------
# Run MCP
# ----------------------------
if __name__ == "__main__":
    mcp.run(transport="sse", port=8000)

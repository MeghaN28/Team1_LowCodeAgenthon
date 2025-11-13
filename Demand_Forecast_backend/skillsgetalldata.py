# inventory_data_mcp.py
# ---------------------------------------
# MCP Agent for fetching all inventory-related data
# Supports Inventory_ID lookup
# ---------------------------------------

import psycopg2
import pandas as pd
from fastmcp import FastMCP

mcp = FastMCP("Inventory Data Agent 📦")

# ----------------------------
# PostgreSQL setup
# ----------------------------
conn = psycopg2.connect(
    host="",
    port="",
    dbname="",
    user="",
    password=""
)
cur = conn.cursor()

# ----------------------------
# Fetch data function
# ----------------------------
def fetch_inventory_data(inventory_id: str):
    inventory_id_clean = inventory_id.strip().upper()
    
    # Fetch from inventory_master
    cur.execute(f"""
        SELECT inventory_id, item_name, item_type, maximum_capacity, initial_stock,
               unit_cost, expiry_date, lead_time_days, avg_daily_consumption, minimum_required, vendor_id
        FROM inventory_master
        WHERE inventory_id = %s
    """, (inventory_id_clean,))
    master = cur.fetchone()
    
    if not master:
        return {"error": f"No data found for inventory ID {inventory_id_clean}"}

    master_cols = [desc[0] for desc in cur.description]
    master_data = dict(zip(master_cols, master))

    # Fetch from inventory_daily
    cur.execute(f"""
        SELECT date, opening_stock, closing_stock, quantity_consumed, quantity_restocked, department_count
        FROM inventory_daily
        WHERE inventory_id = %s
        ORDER BY date DESC
        LIMIT 7
    """, (inventory_id_clean,))
    daily_rows = cur.fetchall()
    daily_cols = [desc[0] for desc in cur.description]
    daily_data = [dict(zip(daily_cols, r)) for r in daily_rows]

    # Fetch from consumption (last 7 days)
    cur.execute(f"""
        SELECT date, quantity_consumed, remaining_stock, department, transaction_id, batch_lot, staff_id, shift
        FROM consumption
        WHERE inventory_id = %s
        ORDER BY date DESC
        LIMIT 7
    """, (inventory_id_clean,))
    consumption_rows = cur.fetchall()
    consumption_cols = [desc[0] for desc in cur.description]
    consumption_data = [dict(zip(consumption_cols, r)) for r in consumption_rows]

    # Fetch from finance (last 5 transactions)
    cur.execute(f"""
        SELECT purchase_date, delivery_date, quantity, unit_cost, total_cost, account_code, vendor_id, invoice_id, payment_status
        FROM finance
        WHERE inventory_id = %s
        ORDER BY purchase_date DESC
        LIMIT 5
    """, (inventory_id_clean,))
    finance_rows = cur.fetchall()
    finance_cols = [desc[0] for desc in cur.description]
    finance_data = [dict(zip(finance_cols, r)) for r in finance_rows]

    # Fetch from inventory_department_mapping
    cur.execute(f"""
        SELECT department_name, team_member, team_member_email, manager, manager_email, min_stock_limit, max_capacity, lead_time_days, vendor_id
        FROM inventory_department_mapping
        WHERE inventory_id = %s
    """, (inventory_id_clean,))
    dept_rows = cur.fetchall()
    dept_cols = [desc[0] for desc in cur.description]
    dept_data = [dict(zip(dept_cols, r)) for r in dept_rows]

    # Fetch vendor info
    vendor_id = master_data.get("vendor_id")
    vendor_data = None
    if vendor_id:
        cur.execute(f"""
            SELECT vendor_id, vendor_name, contact_number, region, vendor_rating, default_lead_time_days
            FROM vendor_master
            WHERE vendor_id = %s
        """, (vendor_id,))
        vendor_row = cur.fetchone()
        if vendor_row:
            vendor_cols = [desc[0] for desc in cur.description]
            vendor_data = dict(zip(vendor_cols, vendor_row))

    # Combine all
    result = {
        "Inventory_Master": master_data,
        "Inventory_Daily": daily_data,
        "Consumption": consumption_data,
        "Finance": finance_data,
        "Department_Mapping": dept_data,
        "Vendor": vendor_data
    }

    return result

# ----------------------------
# MCP Tool
# ----------------------------
@mcp.tool
def get_inventory_details(inventory_id: str):
    if not inventory_id:
        return {"error": "Inventory_ID is required"}
    return fetch_inventory_data(inventory_id)

# ----------------------------
# Run MCP
# ----------------------------
if __name__ == "__main__":
    print("🚀 Inventory Data MCP running...")
    mcp.run(transport="sse", port=8001)

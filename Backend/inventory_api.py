from flask import Flask, Blueprint, jsonify
import psycopg2
import pandas as pd

# Create Flask app
app = Flask(__name__)

# Blueprint
inventory_api = Blueprint('inventory_api', __name__)

# Database connection
def get_db_connection():
    return psycopg2.connect(
  
    )

# Compute stock status safely
def compute_stock_status(row):
    closing_stock = row.get('closing_stock') or 0
    min_stock = row.get('min_stock') or 0
    if closing_stock == 0:
        return 'out-of-stock'
    elif closing_stock <= min_stock:
        return 'low-stock'
    else:
        return 'in-stock'

# API route
@inventory_api.route('/api/inventory', methods=['GET'])
def get_inventory():
    try:
        conn = get_db_connection()
        query = """
            SELECT 
                inventory_id,
                item_type,
                item_name,
                form,
                use,
                vendor_id,
                lead_time_days,
                department_count,
                min_stock,
                max_capacity,
                closing_stock
            FROM public.inventory_master
            ORDER BY item_name ASC;
        """
        df = pd.read_sql(query, conn)
        conn.close()

        # Replace numeric NaN with 0
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)

        # Replace non-numeric NaN with None
        df = df.where(pd.notnull(df), None)

        # Compute stock status
        df['stock_status'] = df.apply(compute_stock_status, axis=1)

        # Rename columns for frontend
        df.rename(columns={'closing_stock': 'current_stock'}, inplace=True)

        # Convert to dict and return JSON
        items = df.to_dict(orient='records')
        return jsonify({"success": True, "items": items})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# Register blueprint
app.register_blueprint(inventory_api)

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

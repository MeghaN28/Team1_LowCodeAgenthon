import psycopg2
import pandas as pd

# --------------------------
# Database connection setup
# --------------------------
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="inventory_database",
    user="meghanarendrasimha",
    password="Welcome@123"
)

# --------------------------
# Query inventory_master
# --------------------------
query = "SELECT * FROM inventory_master ORDER BY inventory_id;"

# Read into pandas DataFrame
df = pd.read_sql(query, conn)

# Close connection
conn.close()

# --------------------------
# Save to CSV
# --------------------------
output_file = "inventory_master_backup.csv"
df.to_csv(output_file, index=False)
print(f"Inventory data saved to '{output_file}' successfully!")

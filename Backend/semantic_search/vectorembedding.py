import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer

# ----------------------------
# PostgreSQL connection
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
# Load embedding model
# ----------------------------
model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 384-dim embeddings

# ----------------------------
# Fetch items without embeddings
# ----------------------------
cur.execute("""
    SELECT inventory_id, item_name 
    FROM inventory_master 
    WHERE embedding IS NULL AND item_name ILIKE '%thermometer%'
""")
rows = cur.fetchall()

for inv_id, item_name in rows:
    # Generate embedding
    emb = model.encode(item_name)
    emb_list_str = '[' + ','.join([str(x) for x in emb.tolist()]) + ']'

    # Update DB
    cur.execute(
        "UPDATE inventory_master SET embedding=%s WHERE inventory_id=%s",
        (emb_list_str, inv_id)
    )

conn.commit()
cur.close()
conn.close()

print(f"Updated embeddings for {len(rows)} thermometer items.")

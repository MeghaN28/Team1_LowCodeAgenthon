from sentence_transformers import SentenceTransformer
import psycopg2
import numpy as np

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')  # produces 384-dim embeddings

conn = psycopg2.connect(
    host="",        # replace with your host
    port="",             # replace with your port
    dbname="",
    user="",
    password="" # replace with your password
)
cur = conn.cursor()

# Fetch items
cur.execute("SELECT inventory_id, item_name FROM inventory_master")
items = cur.fetchall()

for inventory_id, item_name in items:
    emb = model.encode(item_name).tolist()  # list of floats
    emb_str = "[" + ",".join(map(str, emb)) + "]"
    cur.execute("UPDATE inventory_master SET embedding=%s WHERE inventory_id=%s", (emb_str, inventory_id))

conn.commit()
cur.close()
conn.close()
print("✅ Embeddings saved for all items")

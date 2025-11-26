from sentence_transformers import SentenceTransformer
import psycopg2

# Load 128-dimensional model
model = SentenceTransformer('paraphrase-MiniLM-L3-v2')

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="inventory_database",
    user="meghanarendrasimha",
    password="Welcome@123"
)
cur = conn.cursor()

# Fetch inventory items
cur.execute("SELECT inventory_id, item_name, item_type FROM inventory_master")
rows = cur.fetchall()

for inv_id, name, type_ in rows:
    text = f"{name} {type_ or ''}".strip()
    emb = model.encode(text)

    # Safety check for dimension
    if len(emb) != 384:
        print(f"Skipping {text} due to dimension mismatch: {len(emb)}")
        continue

    # Use list directly; psycopg2 + pgvector accepts Python list
    cur.execute(
        "UPDATE inventory_master SET embedding = %s WHERE inventory_id = %s",
        (emb.tolist(), inv_id)
    )

conn.commit()
cur.close()
conn.close()
print("Embeddings updated successfully.")

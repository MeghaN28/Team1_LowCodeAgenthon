# build_inventory_embeddings.py
import psycopg2, numpy as np, pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    dbname="vectordb",
    user="meghanarendrasimha",
    password="Welcome@123"
)
cur = conn.cursor()
cur.execute("SELECT inventory_id, item_name FROM inventory_master")
rows = cur.fetchall()
conn.close()

ids, names = zip(*rows)
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(list(names), show_progress_bar=True, convert_to_numpy=True)

np.save("inventory_ids.npy", np.array(ids))
np.save("inventory_embeddings.npy", embeddings)

index = faiss.IndexFlatIP(embeddings.shape[1])
faiss.normalize_L2(embeddings)
index.add(embeddings)
faiss.write_index(index, "inventory_index.faiss")

print("✅ Inventory embeddings + FAISS index exported.")

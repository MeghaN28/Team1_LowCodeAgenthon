# ----------------------------
# inventory_update.py
# ----------------------------
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
import random
from datetime import datetime, timedelta

# ----------------------------
# PostgreSQL setup
# ----------------------------
conn = psycopg2.connect(
 
)
cur = conn.cursor()

# ----------------------------
# Load SentenceTransformer
# ----------------------------
sem_model = SentenceTransformer('paraphrase-MiniLM-L3-v2')  # 384-dim

# ----------------------------
# Generate 200 unique inventory items
# ----------------------------
items = [
    # Consumables (40)
    ("Syringe 1ml", "Liquid", "Injection", "Consumable"),
    ("Syringe 2ml", "Liquid", "Injection", "Consumable"),
    ("Syringe 5ml", "Liquid", "Injection", "Consumable"),
    ("Syringe 10ml", "Liquid", "Injection", "Consumable"),
    ("Sterile Gloves S", "Gloves", "Hand protection", "Consumable"),
    ("Sterile Gloves M", "Gloves", "Hand protection", "Consumable"),
    ("Sterile Gloves L", "Gloves", "Hand protection", "Consumable"),
    ("Surgical Mask N95", "Mask", "Respiratory protection", "Consumable"),
    ("Surgical Mask Surgical", "Mask", "Respiratory protection", "Consumable"),
    ("IV Set 100ml", "IV Set", "Fluid administration", "Consumable"),
    ("IV Set 250ml", "IV Set", "Fluid administration", "Consumable"),
    ("IV Set 500ml", "IV Set", "Fluid administration", "Consumable"),
    ("Bandage Roll 2cm", "Roll", "Wound dressing", "Consumable"),
    ("Bandage Roll 5cm", "Roll", "Wound dressing", "Consumable"),
    ("Bandage Roll 10cm", "Roll", "Wound dressing", "Consumable"),
    ("Surgical Cap Blue", "Cap", "Head protection", "Consumable"),
    ("Surgical Cap Green", "Cap", "Head protection", "Consumable"),
    ("Alcohol Swab", "Swab", "Skin antiseptic", "Consumable"),
    ("Cotton Roll 50g", "Roll", "Wound dressing", "Consumable"),
    ("Cotton Roll 100g", "Roll", "Wound dressing", "Consumable"),
    ("Urinary Catheter 14Fr", "Catheter", "Urinary drainage", "Consumable"),
    ("Urinary Catheter 16Fr", "Catheter", "Urinary drainage", "Consumable"),
    ("Urinary Catheter 18Fr", "Catheter", "Urinary drainage", "Consumable"),
    ("Disposable Syringe Needle 21G", "Needle", "Injection", "Consumable"),
    ("Disposable Syringe Needle 23G", "Needle", "Injection", "Consumable"),
    ("IV Cannula 18G", "Cannula", "Venous access", "Consumable"),
    ("IV Cannula 20G", "Cannula", "Venous access", "Consumable"),
    ("IV Cannula 22G", "Cannula", "Venous access", "Consumable"),
    ("Sterile Dressing 5x5", "Dressing", "Wound care", "Consumable"),
    ("Sterile Dressing 10x10", "Dressing", "Wound care", "Consumable"),
    ("Gauze Pad 5x5", "Pad", "Wound care", "Consumable"),
    ("Gauze Pad 10x10", "Pad", "Wound care", "Consumable"),
    ("Surgical Tape 1cm", "Tape", "Wound dressing", "Consumable"),
    ("Surgical Tape 2cm", "Tape", "Wound dressing", "Consumable"),
    ("Surgical Tape 5cm", "Tape", "Wound dressing", "Consumable"),
    ("Face Shield", "Shield", "Eye protection", "Consumable"),
    ("Disposable Head Cover", "Cap", "Head protection", "Consumable"),
    ("Surgical Hood", "Hood", "Head protection", "Consumable"),
    ("Sterile Head Cap", "Cap", "Head protection", "Consumable"),
    ("Nebulizer Mask", "Mask", "Respiratory therapy", "Consumable"),
    ("Oxygen Mask Adult", "Mask", "Oxygen delivery", "Consumable"),

    # Medications (80)
    ("Paracetamol 500mg", "Tablet", "Pain relief", "Medication"),
    ("Paracetamol 650mg", "Tablet", "Pain relief", "Medication"),
    ("Ibuprofen 200mg", "Tablet", "Pain relief", "Medication"),
    ("Ibuprofen 400mg", "Tablet", "Pain relief", "Medication"),
    ("Amoxicillin 250mg", "Capsule", "Antibiotic", "Medication"),
    ("Amoxicillin 500mg", "Capsule", "Antibiotic", "Medication"),
    ("Ceftriaxone 1g", "Injection", "Antibiotic", "Medication"),
    ("Ceftriaxone 500mg", "Injection", "Antibiotic", "Medication"),
    ("Azithromycin 250mg", "Tablet", "Antibiotic", "Medication"),
    ("Azithromycin 500mg", "Tablet", "Antibiotic", "Medication"),
    ("Metformin 500mg", "Tablet", "Diabetes", "Medication"),
    ("Metformin 850mg", "Tablet", "Diabetes", "Medication"),
    ("Insulin 10ml", "Injection", "Diabetes", "Medication"),
    ("Insulin 20ml", "Injection", "Diabetes", "Medication"),
    ("Atorvastatin 10mg", "Tablet", "Cardiovascular", "Medication"),
    ("Atorvastatin 20mg", "Tablet", "Cardiovascular", "Medication"),
    ("Amlodipine 5mg", "Tablet", "Cardiovascular", "Medication"),
    ("Amlodipine 10mg", "Tablet", "Cardiovascular", "Medication"),
    ("Omeprazole 20mg", "Capsule", "Antacid", "Medication"),
    ("Omeprazole 40mg", "Capsule", "Antacid", "Medication"),
    ("Pantoprazole 20mg", "Tablet", "Antacid", "Medication"),
    ("Pantoprazole 40mg", "Tablet", "Antacid", "Medication"),
    ("Prednisolone 5mg", "Tablet", "Steroid", "Medication"),
    ("Prednisolone 10mg", "Tablet", "Steroid", "Medication"),
    ("Hydrocortisone 100mg", "Injection", "Steroid", "Medication"),
    ("Hydrocortisone 200mg", "Injection", "Steroid", "Medication"),
    ("Vitamin C 500mg", "Tablet", "Supplement", "Medication"),
    ("Vitamin D 1000 IU", "Tablet", "Supplement", "Medication"),
    ("Calcium 500mg", "Tablet", "Supplement", "Medication"),
    ("Iron 100mg", "Tablet", "Supplement", "Medication"),
    # Add more until 200 items...
]

# ----------------------------
# Function to generate random stock
# ----------------------------
def generate_stock():
    opening = random.randint(50, 200)
    consumed = random.randint(0, min(opening, 20))
    restock = random.randint(0, 50)
    closing = opening - consumed + restock
    return opening, consumed, restock, closing

# ----------------------------
# Update inventory_master
# ----------------------------
for idx, (name, form, use, item_type) in enumerate(items, start=1):
    inventory_id = f"INV{idx:04d}"
    vendor_id = f"VEND{random.randint(1, 20):03d}"
    lead_time_days = random.randint(1, 10)
    department_count = random.randint(1, 5)
    min_stock = random.randint(10, 20)
    max_capacity = random.randint(100, 500)
    opening_stock, consumed, restock, closing_stock = generate_stock()
    out_of_stock = closing_stock <= 0
    low_stock = closing_stock <= min_stock
    date_today = datetime.today().date()

    # Generate embedding
    text_for_embedding = f"{name} {item_type} {form} {use}"
    embedding = sem_model.encode(text_for_embedding).tolist()

    cur.execute("""
        INSERT INTO inventory_master (
            date, inventory_id, opening_stock, quantity_consumed, quantity_restocked,
            closing_stock, vendor_id, lead_time_days, department_count,
            min_stock, max_capacity, item_name, form, use, item_type,
            out_of_stock, low_stock, embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (inventory_id) DO UPDATE SET
            date=EXCLUDED.date,
            opening_stock=EXCLUDED.opening_stock,
            quantity_consumed=EXCLUDED.quantity_consumed,
            quantity_restocked=EXCLUDED.quantity_restocked,
            closing_stock=EXCLUDED.closing_stock,
            vendor_id=EXCLUDED.vendor_id,
            lead_time_days=EXCLUDED.lead_time_days,
            department_count=EXCLUDED.department_count,
            min_stock=EXCLUDED.min_stock,
            max_capacity=EXCLUDED.max_capacity,
            item_name=EXCLUDED.item_name,
            form=EXCLUDED.form,
            use=EXCLUDED.use,
            item_type=EXCLUDED.item_type,
            out_of_stock=EXCLUDED.out_of_stock,
            low_stock=EXCLUDED.low_stock,
            embedding=EXCLUDED.embedding
    """, (
        date_today, inventory_id, opening_stock, consumed, restock, closing_stock,
        vendor_id, lead_time_days, department_count, min_stock, max_capacity,
        name, form, use, item_type, out_of_stock, low_stock, embedding
    ))

conn.commit()
cur.close()
conn.close()
print("✅ Inventory Master updated with 200 unique items and embeddings.")

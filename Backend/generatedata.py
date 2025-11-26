import csv
import random
from datetime import datetime, timedelta

# -----------------------------
# CONFIGURATION
# -----------------------------
NUM_INVENTORY = 500
NUM_VENDORS = 20
NUM_TRANSACTIONS = 1000
NUM_INVOICES = 500
START_DATE = datetime(2025, 8, 1)

# -----------------------------
# Define realistic item mapping: Item_Name -> Form -> Use
# -----------------------------
item_mapping = {
    "Acetaminophen 500mg": ("Tablet", "Pain Relief"),
    "Ibuprofen 200mg": ("Capsule", "Pain Relief"),
    "Amoxicillin 250mg": ("Capsule", "Antibiotic"),
    "Ceftriaxone 1g": ("Injection", "Antibiotic"),
    "Paracetamol Syrup": ("Syrup", "Pain Relief"),
    "Vitamin C 500mg": ("Tablet", "Vitamin"),
    "Insulin 10ml": ("Injection", "Diabetic"),
    "Syringe 5ml": ("Device", "Consumable"),
    "Bandage 2cm": ("Bandage", "Surgical"),
    "Saline 500ml": ("Liquid", "Consumable"),
    "Gauze 10x10cm": ("Bandage", "Surgical"),
    "Gloves Nitrile": ("Device", "Consumable"),
    "Face Mask": ("Device", "Consumable"),
    "Antiseptic Solution": ("Liquid", "Surgical"),
    "Stethoscope": ("Device", "Medical Equipment"),
    "Thermometer": ("Device", "Medical Equipment"),
    "Oximeter": ("Device", "Medical Equipment"),
    "IV Set": ("Device", "Consumable"),
    "Scalpel": ("Device", "Surgical"),
    "Surgical Cap": ("Device", "Surgical")
}

item_names = list(item_mapping.keys())

# -----------------------------
# Generate Vendor Master
# -----------------------------
vendor_ids = [f"VEND{i:03d}" for i in range(1, NUM_VENDORS+1)]
regions = ["North", "South", "East", "West", "Central"]

with open("vendor_master.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Vendor_ID", "Vendor_Name", "Contact_Number", "Default_Lead_Time_days", "Region", "Vendor_Rating"])
    for i in range(NUM_VENDORS):
        writer.writerow([
            vendor_ids[i],
            f"Vendor_{i+1:03d}",
            f"+1{random.randint(1000000000,9999999999)}",
            random.randint(2, 10),
            random.choice(regions),
            round(random.uniform(1,5), 1)
        ])

# -----------------------------
# Generate Inventory Master
# -----------------------------
with open("inventory_master.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Date","Inventory_ID","Opening_Stock","Quantity_Consumed","Quantity_Restocked","Closing_Stock",
        "Vendor_ID","Lead_Time_Days","Department_Count","Min Stock","Max Capacity","Item_Name","Form","Use"
    ])
    for i in range(1, NUM_INVENTORY+1):
        inventory_id = f"INV{i:05d}"
        opening_stock = random.randint(50, 500)
        qty_consumed = random.randint(0, 50)
        qty_restocked = random.randint(0, 100)
        closing_stock = opening_stock - qty_consumed + qty_restocked
        item = random.choice(item_names)
        form, use = item_mapping[item]
        writer.writerow([
            (START_DATE + timedelta(days=random.randint(0,30))).strftime("%d-%m-%Y"),
            inventory_id,
            opening_stock,
            qty_consumed,
            qty_restocked,
            closing_stock,
            random.choice(vendor_ids),
            random.randint(1,10),
            random.randint(1,5),
            random.randint(10,50),
            random.randint(100,1000),
            item,
            form,
            use
        ])

# -----------------------------
# Generate Consumption
# -----------------------------
shifts = ["Morning", "Afternoon", "Night"]
departments = ["ER", "ICU", "General", "Pediatrics", "Surgery"]

with open("consumption.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Transaction_ID","Date","Inventory_ID","Quantity_Consumed","Department",
        "Staff_ID","Shift","Consumption_Reason","Remaining_Stock","Batch_Lot"
    ])
    for i in range(1, NUM_TRANSACTIONS+1):
        inventory_id = f"INV{random.randint(1, NUM_INVENTORY):05d}"
        qty_consumed = random.randint(1, 20)
        remaining = random.randint(0, 500)
        writer.writerow([
            f"TXN{i:06d}",
            (START_DATE + timedelta(days=random.randint(0,30))).strftime("%d-%m-%Y"),
            inventory_id,
            qty_consumed,
            random.choice(departments),
            f"STF{random.randint(1000,9999)}",
            random.choice(shifts),
            random.choice(["Routine Use", "Emergency Use"]),
            remaining,
            f"LOT{random.randint(10000,99999)}"
        ])

# -----------------------------
# Generate Finance
# -----------------------------
with open("finance.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Invoice_ID","Vendor_ID","Inventory_ID","Purchase_Date","Quantity",
        "Unit_Cost","Total_Cost","Payment_Status","Account_Code","Delivery_Date"
    ])
    for i in range(1, NUM_INVOICES+1):
        inventory_id = f"INV{random.randint(1, NUM_INVENTORY):05d}"
        vendor_id = random.choice(vendor_ids)
        qty = random.randint(10, 200)
        unit_cost = random.randint(1, 20)
        total_cost = qty * unit_cost
        writer.writerow([
            f"INVF{i:06d}",
            vendor_id,
            inventory_id,
            (START_DATE + timedelta(days=random.randint(0,30))).strftime("%d-%m-%Y"),
            qty,
            unit_cost,
            total_cost,
            random.choice(["Paid","Pending","Overdue"]),
            f"ACCT{random.randint(100,999)}",
            (START_DATE + timedelta(days=random.randint(31,60))).strftime("%d-%m-%Y")
        ])

print("Generated CSVs: inventory_master.csv, vendor_master.csv, consumption.csv, finance.csv")

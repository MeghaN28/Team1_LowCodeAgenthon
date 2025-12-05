from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# Receipt items
receipts = [
    ("thermometer", 2),
    ("Atorvastatin 20mg", 3),
    ("Bandage Roll 5cm", 3),
    ("Sterile Head Cap", 3)
]

# Today's date
today = datetime.today().strftime("%Y-%m-%d")

# Generate PDFs
for idx, (item_name, qty) in enumerate(receipts, start=1):
    filename = f"receipt_{idx}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, f"Receipt #{idx}")

    # Date
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, f"Date: {today}")

    # Item details
    c.drawString(50, height - 130, f"Item: {item_name}")
    c.drawString(50, height - 160, f"Quantity: {qty}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, "Thank you for your purchase!")

    c.showPage()
    c.save()
    print(f"Generated: {filename}")

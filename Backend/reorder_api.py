# reorder_api.py
from flask import Blueprint, request, jsonify
import psycopg2
import psycopg2.extras

reorder_api = Blueprint("reorder_api", __name__)

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5432",
        dbname="medical_inventory_db",
        user="meghanarendrasimha",
        password="Welcome@123"
    )

# Internal helper function (not a route)
def log_reorder(inventory_id, item_name, reorder_qty, current_stock,
                status="PENDING", email_recipient=None,
                email_subject=None, email_body=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        INSERT INTO reorder_log (
            inventory_id, item_name, reorder_quantity,
            current_stock, status, email_recipient,
            email_subject, email_body, created_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        RETURNING log_id;
    """
    cur.execute(query, (
        inventory_id, item_name, reorder_qty, current_stock,
        status, email_recipient, email_subject, email_body
    ))
    log_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return log_id

# GET all logs
@reorder_api.route("/reorder-log", methods=["GET"])
def get_reorder_logs():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM reorder_log ORDER BY created_at DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows), 200

# POST a new log
@reorder_api.route("/reorder-log", methods=["POST"])
def create_reorder_log():
    data = request.get_json()
    required = ["inventory_id", "item_name", "reorder_quantity", "current_stock"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    log_id = log_reorder(
        inventory_id=data["inventory_id"],
        item_name=data["item_name"],
        reorder_qty=data["reorder_quantity"],
        current_stock=data["current_stock"],
        status=data.get("status", "PENDING"),
        email_recipient=data.get("email_recipient"),
        email_subject=data.get("email_subject"),
        email_body=data.get("email_body")
    )
    return jsonify({"success": True, "log_id": log_id}), 201

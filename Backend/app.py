# app.py
from flask import Flask
from flask_cors import CORS

from inventory_api import inventory_api
from tts_api import tts_bp
from purchase_api import purchase_api
from reorder_api import reorder_api

app = Flask(__name__)

# FIX: Enable full CORS including preflight
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

@app.route("/")
def index():
    return {"message": "Inventory API running!"}

# Register endpoints with prefixes
app.register_blueprint(inventory_api)
app.register_blueprint(tts_bp, url_prefix="/api")
app.register_blueprint(purchase_api, url_prefix="/api/purchase")
app.register_blueprint(reorder_api, url_prefix="/api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

# app.py
from flask import Flask
from flask_cors import CORS

from inventory_api import inventory_api   # Make sure this exists
from tts_api import tts_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(inventory_api)        # /inventory routes
app.register_blueprint(tts_bp, url_prefix="/api")  # /api/tts

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

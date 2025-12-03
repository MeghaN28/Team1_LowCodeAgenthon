import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

purchase_api = Blueprint("purchase_api", __name__)

# Support images + PDFs
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
UPLOAD_FOLDER = os.path.expanduser("~/Documents/receipts")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@purchase_api.route("/upload_bulk", methods=["POST"])
def upload_bulk():
    if 'files' not in request.files:
        return jsonify({"success": False, "error": "No files part"}), 400

    files = request.files.getlist('files')
    saved_files = []

    for file in files:
        if file.filename == '':
            continue
        if not allowed_file(file.filename):
            continue

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        saved_files.append(filename)

    if not saved_files:
        return jsonify({"success": False, "error": "No valid files uploaded"}), 400

    return jsonify({"success": True, "files": saved_files})

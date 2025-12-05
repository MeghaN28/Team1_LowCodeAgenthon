# tts_api.py
import os
import subprocess
import uuid
import tempfile
import shutil
from flask import Blueprint, request, send_file, jsonify
from flask_cors import cross_origin

tts_bp = Blueprint("tts_bp", __name__)

@tts_bp.route("/tts", methods=["POST", "OPTIONS"])
@cross_origin()   # IMPORTANT FIX: Enables CORS for this route
def tts_endpoint():
    # Handle CORS preflight automatically
    if request.method == "OPTIONS":
        return jsonify({"status": "OK"}), 200

    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    # Ensure macOS utilities exist
    if not shutil.which("say") or not shutil.which("afconvert"):
        return jsonify({"error": "macOS 'say' or 'afconvert' missing"}), 500

    temp_dir = tempfile.gettempdir()
    uid = uuid.uuid4().hex
    aiff_path = os.path.join(temp_dir, f"tts_{uid}.aiff")
    wav_path = os.path.join(temp_dir, f"tts_{uid}.wav")

    try:
        subprocess.check_call(["say", "-o", aiff_path, text])

        subprocess.check_call([
            "afconvert", "-f", "WAVE", "-d", "LEI16@22050",
            aiff_path, wav_path
        ])

        return send_file(
            wav_path,
            mimetype="audio/wav",
            as_attachment=False,
            download_name="speech.wav"
        )

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"TTS process failed: {e}"}), 500

    finally:
        try:
            if os.path.exists(aiff_path):
                os.remove(aiff_path)
        except:
            pass

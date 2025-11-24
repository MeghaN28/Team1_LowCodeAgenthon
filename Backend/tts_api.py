# tts_api.py
import os
import subprocess
import uuid
import tempfile
from flask import Blueprint, request, jsonify, send_file

tts_bp = Blueprint("tts_bp", __name__)

@tts_bp.route("/tts", methods=["POST"])
def tts_endpoint():
    """
    POST JSON: { "text": "Hello world" }
    Returns: audio/wav file
    """
    data = request.get_json(silent=True)
    if not data or "text" not in data:
        return jsonify({"error": "No text provided"}), 400

    text = data["text"].strip()
    if not text:
        return jsonify({"error": "Empty text"}), 400

    # Make sure macOS utilities are present
    import shutil
    if not shutil.which("say") or not shutil.which("afconvert"):
        return jsonify({"error": "TTS requires macOS 'say' and 'afconvert' utilities."}), 500

    temp_dir = tempfile.gettempdir()
    uid = uuid.uuid4().hex
    aiff_path = os.path.join(temp_dir, f"tts_{uid}.aiff")
    wav_path = os.path.join(temp_dir, f"tts_{uid}.wav")

    try:
        # generate AIFF using say
        subprocess.check_call(["say", "-o", aiff_path, text])

        # convert AIFF -> WAV (16-bit, 22050Hz)
        subprocess.check_call([
            "afconvert", "-f", "WAVE", "-d", "LEI16@22050", aiff_path, wav_path
        ])

        # return WAV file
        return send_file(wav_path, mimetype="audio/wav", as_attachment=False)

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"TTS process failed: {e}"}), 500

    finally:
        # cleanup AIFF only; WAV will be streamed
        try:
            if os.path.exists(aiff_path):
                os.remove(aiff_path)
        except Exception:
            pass

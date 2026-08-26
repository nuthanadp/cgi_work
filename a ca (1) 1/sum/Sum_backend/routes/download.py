from flask import Blueprint, request, jsonify, send_file
import io
import json
from routes.utils import token_required

download_bp = Blueprint("download", __name__)

@download_bp.route("/download", methods=["POST"])
@token_required
def download():
    # The incoming data is the analysis JSON object
    data = request.json

    # Convert the JSON data to a string with nice formatting
    content = json.dumps(data, indent=2)

    buf = io.BytesIO()
    buf.write(content.encode("utf-8"))
    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name="document_analysis.json",  # Changed to .json
        mimetype="application/json"              # Changed to JSON mimetype
    )

@download_bp.route("/download_transcript", methods=["POST"])
@token_required
def download_transcript():
    # The incoming data is already the analysis JSON we want
    data = request.json

    # Convert the JSON data to a formatted string
    content = json.dumps(data, indent=2)
    
    buf = io.BytesIO()
    buf.write(content.encode("utf-8"))
    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name="transcript_analysis.json", # Changed to .json
        mimetype="application/json"               # Changed to JSON mimetype
    )
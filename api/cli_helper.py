# api/cli_helper.py — CLI Command Converter API
# Bridges cmd-convertor logic into the dashboard Flask backend.
# Reuses the existing CLIConverter class + smart API routing from cmd-convertor.

import sys
import os
from pathlib import Path
from flask import Blueprint, request, jsonify
from api.auth import login_required

# ─── Bootstrap cmd-convertor's env (so it can find its own .env) ────────────────
# cmd-convertor lives at: api/engines/cmd-convertor/
# We add it to sys.path so 'from config import ...' and 'from core import ...' work
_cmd_conv_dir = Path(__file__).parent / "engines" / "cmd-convertor"
if str(_cmd_conv_dir) not in sys.path:
    sys.path.insert(0, str(_cmd_conv_dir))

from config import API_KEY, BASE_URL, MODEL_NAME, ACTIVE_PROVIDER
from core import CLIConverter, MiniMaxAPIError, detect_intent

cli_helper_bp = Blueprint("cli_helper", __name__)


@cli_helper_bp.route("/api/cli-helper/convert", methods=["POST"])
@login_required
def cli_convert():
    """Convert a CLI command or NL workflow to multiple shells."""
    data = request.json
    command = data.get("command", "").strip()

    if not command:
        return jsonify({"error": "กรุณาพิมพ์คำสั่งที่ต้องการแปลง"}), 400

    if len(command.strip()) < 2:
        return jsonify({"error": "คำสั่งสั้นเกินไป กรุณาลองใหม่"}), 400

    intent = detect_intent(command)

    try:
        converter = CLIConverter(
            api_key=API_KEY,
            base_url=BASE_URL,
            model=MODEL_NAME,
        )
        answer = converter.convert(command)

        return jsonify({
            "success": True,
            "answer": answer,
            "provider": ACTIVE_PROVIDER,
            "intent": intent,
            "model": MODEL_NAME,
        })

    except MiniMaxAPIError as e:
        return jsonify({"error": str(e)}), 502
    except Exception as e:
        return jsonify({"error": f"เกิดข้อผิดพลาด: {str(e)}"}), 500

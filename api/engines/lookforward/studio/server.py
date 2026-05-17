import os
import subprocess
import json
import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StudioServer")

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        "status": "online",
        "project": "lookforward",
        "engine": "Gemini 2.5 Flash"
    })

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Scan data/09_ReadyToPost for recent posts."""
    posts = []
    ready_dir = DATA_DIR / "09_ReadyToPost"
    if ready_dir.exists():
        for date_folder in sorted(ready_dir.iterdir(), reverse=True):
            if not date_folder.is_dir(): continue
            for post_folder in sorted(date_folder.iterdir(), reverse=True):
                if not post_folder.is_dir(): continue
                
                metadata_path = post_folder / "_metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                            posts.append({
                                "id": post_folder.name,
                                "date": date_folder.name,
                                "topic": meta.get("topic", post_folder.name),
                                "status": "Ready",
                                "score": meta.get("insight_score", "?")
                            })
                    except Exception as e:
                        logger.error(f"Error reading {metadata_path}: {e}")

    return jsonify(posts[:20])

@app.route('/api/posts/<date_str>/<post_id>', methods=['GET'])
def get_post_details(date_str, post_id):
    """Fetch full content of a specific post."""
    post_dir = DATA_DIR / "09_ReadyToPost" / date_str / post_id
    if not post_dir.exists():
        return jsonify({"error": "Post not found"}), 404

    details = {
        "id": post_id,
        "date": date_str,
        "body": "",
        "caption": "",
        "hashtags": "",
        "images": []
    }

    # Read files
    file_map = {
        "post.txt": "body",
        "caption.txt": "caption",
        "hashtags.txt": "hashtags"
    }

    for filename, key in file_map.items():
        path = post_dir / filename
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    details[key] = f.read()
            except Exception as e:
                logger.error(f"Error reading {path}: {e}")

    # Scan media
    media_dir = post_dir / "media"
    if media_dir.exists():
        for img_file in media_dir.iterdir():
            if img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                # Return URL for the image
                details["images"].append(f"http://127.0.0.1:5000/api/media/{date_str}/{post_id}/{img_file.name}")

    return jsonify(details)

@app.route('/api/media/<date_str>/<post_id>/<filename>')
def serve_media(date_str, post_id, filename):
    """Serve images from the project data directory."""
    directory = DATA_DIR / "09_ReadyToPost" / date_str / post_id / "media"
    return send_from_directory(str(directory), filename)

@app.route('/api/ignite', methods=['POST'])
def ignite_analysis():
    """Execute the pipeline script."""
    data = request.json
    topic = data.get('topic')
    
    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    try:
        script_path = SCRIPTS_DIR / "run_pipeline_gemini.py"
        logger.info(f"Igniting analysis for topic: {topic}")
        
        # Use subprocess to run the script with a 60s timeout
        try:
            result = subprocess.run(
                ["python", str(script_path), topic, "--gen-images"],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=60
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"Pipeline timed out after 60s for topic: {topic}")
            return jsonify({
                "status": "error",
                "message": "ANALYSIS TIMEOUT: The AI process took too long (>60s). Please try a simpler topic or check system load."
            }), 504
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "output": result.stdout,
                "message": f"Successfully ignited analysis for: {topic}"
            })
        else:
            logger.error(f"Pipeline failed: {result.stderr}")
            return jsonify({
                "status": "error",
                "output": result.stdout,
                "error": result.stderr
            }), 500
            
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)

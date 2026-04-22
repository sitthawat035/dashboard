"""
api/reports_api.py — Engine Reports API
GET /api/reports/scan — Scan all engines and return structured report data
"""

import json
import os
from pathlib import Path
from flask import Blueprint, jsonify

reports_bp = Blueprint("reports", __name__)

ENGINES_DIR = Path(__file__).parent / "engines"


@reports_bp.route("/api/reports/scan", methods=["GET"])
def scan_engines():
    """Scan all engine outputs and return structured JSON report."""
    result = {}

    # ── LookForward ──
    result["lookforward"] = _scan_lookforward()

    # ── Trend Scan ──
    result["trend_scan"] = _scan_trend_scan()

    # ── VEO Gen ──
    result["veo_gen"] = _scan_veo_gen()

    # ── Shopee ──
    result["shopee"] = _scan_shopee()

    # ── Image Gen ──
    result["image_gen"] = _scan_image_gen()

    # ── Social ──
    result["social"] = _scan_social()

    from datetime import datetime
    result["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(result)


def _scan_lookforward():
    pipeline_history = ENGINES_DIR / "lookforward" / ".agent" / "pipeline_history"
    ready_dir = ENGINES_DIR / "data" / "output" / "lookforward" / "ready_to_post"
    drafts_dir = ENGINES_DIR / "data" / "output" / "lookforward" / "drafts"

    # Pipeline history
    recent_pipelines = []
    if pipeline_history.exists():
        for hf in sorted(pipeline_history.glob("*.json")):
            try:
                with open(hf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                recent_pipelines.append({
                    "run_id": data.get("run_id", hf.stem),
                    "status": data.get("status", "unknown"),
                    "topic": data.get("topic", "N/A"),
                    "created": data.get("created_at", "N/A"),
                })
            except Exception:
                pass

    # Ready to post
    ready_posts = []
    if ready_dir.exists():
        for date_dir in sorted(ready_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                posts = []
                for post_dir in date_dir.iterdir():
                    if post_dir.is_dir():
                        meta = {}
                        meta_file = post_dir / "_metadata.json"
                        if meta_file.exists():
                            try:
                                with open(meta_file, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                            except Exception:
                                pass
                        posts.append({
                            "name": post_dir.name[:80],
                            "has_caption": (post_dir / "caption.txt").exists(),
                            "has_post": (post_dir / "post.txt").exists(),
                            "has_hashtags": (post_dir / "hashtags.txt").exists(),
                            "has_images": (post_dir / "media").exists(),
                            "insight_score": meta.get("insight_score", "-"),
                        })
                ready_posts.append({
                    "date": date_dir.name,
                    "count": len(posts),
                    "posts": posts,
                })

    # Drafts
    draft_dates = []
    if drafts_dir.exists():
        for date_dir in sorted(drafts_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                count = sum(1 for d in date_dir.iterdir() if d.is_dir())
                draft_dates.append({"date": date_dir.name, "count": count})

    return {
        "ready_to_post": ready_posts,
        "drafts": draft_dates,
        "pipeline_count": len(recent_pipelines),
        "recent_pipelines": recent_pipelines,
    }


def _scan_trend_scan():
    trends_file = ENGINES_DIR / "trend_scan" / "latest_trends.json"
    if not trends_file.exists():
        return {"date": "N/A", "niche": "N/A", "topics_count": 0, "topics": []}
    try:
        with open(trends_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        topics = []
        for t in data.get("lookforward_topics", []):
            topics.append({
                "topic": t.get("topic", "")[:100],
                "reason": t.get("reason", "")[:120],
            })
        return {
            "date": data.get("date", "N/A"),
            "niche": data.get("niche_label", "N/A"),
            "topics_count": len(topics),
            "topics": topics,
        }
    except Exception:
        return {"date": "N/A", "niche": "N/A", "topics_count": 0, "topics": []}


def _scan_veo_gen():
    veo = ENGINES_DIR / "veo_gen"
    if not veo.exists():
        return {"scripts_count": 0, "screenshots_count": 0, "has_walkthrough": False, "has_config": False}
    scripts = list(veo.glob("*.py"))
    screenshots = list(veo.glob("*.png"))
    return {
        "scripts_count": len(scripts),
        "screenshots_count": len(screenshots),
        "has_walkthrough": (veo / "walkthrough.md").exists(),
        "has_config": (veo / "config.json").exists(),
    }


def _scan_shopee():
    shopee = ENGINES_DIR / "shopee"
    if not shopee.exists():
        return {"tools_count": 0, "steps_count": 0, "has_cookies": False, "last_error": None}
    tools_dir = shopee / "tools"
    steps_dir = shopee / "scripts" / "steps"
    tools = list(tools_dir.glob("*")) if tools_dir.exists() else []
    steps = list(steps_dir.glob("*")) if steps_dir.exists() else []

    last_error = None
    error_log = shopee / "pipeline_error.log"
    if error_log.exists():
        try:
            with open(error_log, "r", encoding="utf-8") as f:
                last_error = f.read().strip()[:200]
        except Exception:
            pass

    return {
        "tools_count": len(tools),
        "steps_count": len(steps),
        "has_cookies": (shopee / "shopee_cookies.json").exists(),
        "last_error": last_error,
    }


def _scan_image_gen():
    img = ENGINES_DIR / "image_gen"
    scripts = list(img.glob("*.py")) if img.exists() else []
    return {"scripts_count": len(scripts)}


def _scan_social():
    social = ENGINES_DIR / "social"
    scripts = list(social.glob("*.py")) if social.exists() else []
    return {"scripts_count": len(scripts)}

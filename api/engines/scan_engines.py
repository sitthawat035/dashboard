#!/usr/bin/env python3
"""
Engine Output Collector — สแกนทุก engine ใน dashboard แล้วสร้าง report.md
Usage: python scan_engines.py
Output: ../engines_output/YYYY-MM-DD_engine_report.md
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path

# === CONFIG ===
ENGINES_DIR = Path(__file__).parent
OUTPUT_DIR = Path(__file__).parent.parent / "engines_output"
TODAY = datetime.now().strftime("%Y-%m-%d")

ENGINE_DIRS = {
    "lookforward": ENGINES_DIR / "lookforward",
    "shopee": ENGINES_DIR / "shopee",
    "image_gen": ENGINES_DIR / "image_gen",
    "social": ENGINES_DIR / "social",
    "trend_scan": ENGINES_DIR / "trend_scan",
    "veo_gen": ENGINES_DIR / "veo_gen",
}

DATA_OUTPUT = ENGINES_DIR / "data" / "output"


def count_files(path, ext="*"):
    """นับจำนวนไฟล์ใน directory"""
    if not path.exists():
        return 0
    return len(list(path.rglob(f"*.{ext}"))) if ext != "*" else len(list(path.rglob("*")))


def get_dir_size_mb(path):
    """คำนวณขนาด folder (MB)"""
    if not path.exists():
        return 0
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(total / (1024 * 1024), 2)


def scan_lookforward():
    """สแกน output ของ LookForward engine"""
    results = []
    pipeline_history = ENGINES_DIR / "lookforward" / ".agent" / "pipeline_history"
    ready_dir = DATA_OUTPUT / "lookforward" / "ready_to_post"
    drafts_dir = DATA_OUTPUT / "lookforward" / "drafts"

    # Pipeline history
    history_files = sorted(pipeline_history.glob("*.json")) if pipeline_history.exists() else []
    for hf in history_files:
        try:
            with open(hf, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append({
                "run_id": data.get("run_id", hf.stem),
                "topic": data.get("topic", "N/A"),
                "status": data.get("status", "unknown"),
                "created": data.get("created_at", "N/A"),
                "steps": list(data.get("step_results", {}).keys()),
            })
        except:
            pass

    # Ready to post (by date)
    ready_posts = []
    if ready_dir.exists():
        for date_dir in sorted(ready_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                posts_in_date = []
                for post_dir in date_dir.iterdir():
                    if post_dir.is_dir():
                        meta_file = post_dir / "_metadata.json"
                        meta = {}
                        if meta_file.exists():
                            try:
                                with open(meta_file, "r", encoding="utf-8") as f:
                                    meta = json.load(f)
                            except:
                                pass
                        has_images = (post_dir / "media").exists()
                        posts_in_date.append({
                            "name": post_dir.name[:60],
                            "has_caption": (post_dir / "caption.txt").exists(),
                            "has_post": (post_dir / "post.txt").exists(),
                            "has_hashtags": (post_dir / "hashtags.txt").exists(),
                            "has_images": has_images,
                            "insight_score": meta.get("insight_score", "-"),
                        })
                ready_posts.append({
                    "date": date_dir.name,
                    "count": len(posts_in_date),
                    "posts": posts_in_date,
                })

    # Drafts
    draft_dates = []
    if drafts_dir.exists():
        for date_dir in sorted(drafts_dir.iterdir(), reverse=True):
            if date_dir.is_dir():
                draft_count = sum(1 for d in date_dir.iterdir() if d.is_dir())
                draft_dates.append({"date": date_dir.name, "count": draft_count})

    return {"pipelines": results, "ready_to_post": ready_posts, "drafts": draft_dates}


def scan_trend_scan():
    """สแกน output ของ Trend Scan engine"""
    trends_file = ENGINES_DIR / "trend_scan" / "latest_trends.json"
    trend_history = ENGINES_DIR / "trend_history.json"

    trends = []
    if trends_file.exists():
        try:
            with open(trends_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            topics = data.get("lookforward_topics", [])
            for t in topics:
                trends.append({"topic": t.get("topic", "")[:80], "reason": t.get("reason", "")[:100]})
            return {
                "date": data.get("date", "N/A"),
                "niche": data.get("niche_label", "N/A"),
                "topics_count": len(topics),
                "topics": trends,
            }
        except:
            pass
    return {"date": "N/A", "topics_count": 0, "topics": []}


def scan_veo_gen():
    """สแกน output ของ VEO Gen engine"""
    veo_dir = ENGINE_DIRS["veo_gen"]
    scripts = list(veo_dir.glob("*.py"))
    screenshots = list(veo_dir.glob("*.png"))
    discovery = list((veo_dir / "_discovery").glob("*")) if (veo_dir / "_discovery").exists() else []

    return {
        "scripts": [s.name for s in scripts],
        "screenshots_count": len(screenshots),
        "screenshots": [s.name for s in screenshots],
        "discovery_files": len(discovery),
        "has_walkthrough": (veo_dir / "walkthrough.md").exists(),
        "has_config": (veo_dir / "config.json").exists(),
    }


def scan_shopee():
    """สแกน output ของ Shopee engine"""
    shopee_dir = ENGINE_DIRS["shopee"]
    error_log = shopee_dir / "pipeline_error.log"

    error_msg = None
    if error_log.exists():
        try:
            with open(error_log, "r", encoding="utf-8") as f:
                error_msg = f.read().strip()
        except:
            pass

    tools = list((shopee_dir / "tools").glob("*")) if (shopee_dir / "tools").exists() else []
    scripts = list((shopee_dir / "scripts" / "steps").glob("*")) if (shopee_dir / "scripts" / "steps").exists() else []

    return {
        "tools_count": len(tools),
        "tools": [t.name for t in tools],
        "steps_count": len(scripts),
        "steps": [s.name for s in scripts],
        "has_cookies": (shopee_dir / "shopee_cookies.json").exists(),
        "last_error": error_msg,
    }


def scan_image_gen():
    """สแกน output ของ Image Gen engine"""
    img_dir = ENGINE_DIRS["image_gen"]
    scripts = list(img_dir.glob("*.py"))
    return {
        "scripts": [s.name for s in scripts],
        "status": "มี generator script แต่ยังไม่มี output folder",
    }


def scan_social():
    """สแกน output ของ Social engine"""
    social_dir = ENGINE_DIRS["social"]
    scripts = list(social_dir.glob("*.py"))
    return {
        "scripts": [s.name for s in scripts],
        "status": "มี facebook_poster.py — ใช้ร่วมกับ lookforward/shopee pipeline",
    }


def generate_report():
    """สร้าง markdown report"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{TODAY}_engine_report.md"

    lf = scan_lookforward()
    ts = scan_trend_scan()
    veo = scan_veo_gen()
    shopee = scan_shopee()
    img = scan_image_gen()
    social = scan_social()

    lines = []
    lines.append(f"# 🤖 Engine Output Report — {TODAY}")
    lines.append(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")

    # === LOOKFORWARD ===
    lines.append("---")
    lines.append("## 📰 LookForward Engine\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    for rtp in lf["ready_to_post"]:
        lines.append(f"| Ready to Post ({rtp['date']}) | **{rtp['count']}** posts |")
    for d in lf["drafts"]:
        lines.append(f"| Drafts ({d['date']}) | {d['count']} items |")
    lines.append(f"| Pipeline Runs | {len(lf['pipelines'])} |")
    lines.append("")

    if lf["ready_to_post"]:
        lines.append("### ✅ Ready to Post\n")
        for rtp in lf["ready_to_post"]:
            lines.append(f"#### 📅 {rtp['date']} ({rtp['count']} posts)\n")
            for p in rtp["posts"]:
                icons = []
                if p["has_caption"]: icons.append("📝")
                if p["has_post"]: icons.append("📄")
                if p["has_hashtags"]: icons.append("#️⃣")
                if p["has_images"]: icons.append("🖼️")
                lines.append(f"- {' '.join(icons)} `{p['name']}` (score: {p['insight_score']})")
            lines.append("")

    if lf["pipelines"]:
        lines.append("### 🔄 Pipeline History\n")
        lines.append("| Run ID | Status | Topic | Created |")
        lines.append("|--------|--------|-------|---------|")
        for p in lf["pipelines"][-10:]:  # last 10
            topic_short = p["topic"][:50] + "..." if len(p["topic"]) > 50 else p["topic"]
            status_icon = "✅" if p["status"] == "completed" else "❌" if p["status"] == "failed" else "⏳"
            lines.append(f"| `{p['run_id']}` | {status_icon} {p['status']} | {topic_short} | {p['created'][:16]} |")
        lines.append("")

    # === TREND SCAN ===
    lines.append("---")
    lines.append("## 📊 Trend Scan Engine\n")
    lines.append(f"- **Date:** {ts['date']}")
    lines.append(f"- **Niche:** {ts.get('niche', 'N/A')}")
    lines.append(f"- **Topics Found:** {ts['topics_count']}\n")
    if ts["topics"]:
        lines.append("| # | Topic | Reason |")
        lines.append("|---|-------|--------|")
        for i, t in enumerate(ts["topics"], 1):
            lines.append(f"| {i} | {t['topic']} | {t['reason'][:80]}... |")
        lines.append("")

    # === VEO GEN ===
    lines.append("---")
    lines.append("## 🎬 VEO Gen Engine (Google Flow)\n")
    lines.append(f"- **Scripts:** {len(veo['scripts'])}")
    lines.append(f"- **Screenshots:** {veo['screenshots_count']}")
    lines.append(f"- **Discovery Files:** {veo['discovery_files']}")
    lines.append(f"- **Has Walkthrough:** {'✅' if veo['has_walkthrough'] else '❌'}")
    lines.append(f"- **Has Config:** {'✅' if veo['has_config'] else '❌'}\n")
    if veo["scripts"]:
        lines.append("**Pipeline Scripts:**")
        for s in veo["scripts"]:
            lines.append(f"- `{s}`")
        lines.append("")
    if veo["screenshots"]:
        lines.append("**Screenshots (progress tracking):**")
        for s in veo["screenshots"]:
            lines.append(f"- `{s}`")
        lines.append("")

    # === SHOPEE ===
    lines.append("---")
    lines.append("## 🛒 Shopee Engine\n")
    lines.append(f"- **Tools:** {shopee['tools_count']}")
    lines.append(f"- **Pipeline Steps:** {shopee['steps_count']}")
    lines.append(f"- **Has Cookies:** {'✅' if shopee['has_cookies'] else '❌'}")
    if shopee["last_error"]:
        lines.append(f"- ⚠️ **Last Error:** `{shopee['last_error'][:100]}`")
    lines.append("")
    if shopee["tools"]:
        lines.append("**Tools:**")
        for t in shopee["tools"]:
            lines.append(f"- `{t}`")
        lines.append("")
    if shopee["steps"]:
        lines.append("**Pipeline Steps:**")
        for s in shopee["steps"]:
            lines.append(f"- `{s}`")
        lines.append("")

    # === IMAGE GEN ===
    lines.append("---")
    lines.append("## 🖼️ Image Gen Engine\n")
    lines.append(f"- **Status:** {img['status']}")
    lines.append(f"- **Scripts:** {', '.join(img['scripts']) if img['scripts'] else 'None'}\n")

    # === SOCIAL ===
    lines.append("---")
    lines.append("## 📱 Social Engine\n")
    lines.append(f"- **Status:** {social['status']}")
    lines.append(f"- **Scripts:** {', '.join(social['scripts']) if social['scripts'] else 'None'}\n")

    # === SUMMARY ===
    lines.append("---")
    lines.append("## 📋 Summary\n")
    total_posts = sum(r["count"] for r in lf["ready_to_post"])
    total_drafts = sum(d["count"] for d in lf["drafts"])
    lines.append(f"| Engine | Status | Output |")
    lines.append(f"|--------|--------|--------|")
    lines.append(f"| LookForward | ✅ Active | {total_posts} ready, {total_drafts} drafts |")
    lines.append(f"| Trend Scan | ✅ Active | {ts['topics_count']} topics (latest) |")
    lines.append(f"| VEO Gen | 🔧 Development | {veo['screenshots_count']} screenshots |")
    lines.append(f"| Shopee | ⚠️ Needs Playwright | {shopee['tools_count']} tools |")
    lines.append(f"| Image Gen | 🔧 Basic | {len(img['scripts'])} script(s) |")
    lines.append(f"| Social | ✅ Active | {len(social['scripts'])} script(s) |")
    lines.append("")

    report = "\n".join(lines)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Report saved to: {output_file}")
    print(f"📊 Summary: {total_posts} ready posts, {total_drafts} drafts, {ts['topics_count']} trends")
    return output_file


if __name__ == "__main__":
    generate_report()

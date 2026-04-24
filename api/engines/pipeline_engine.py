#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
import time

import json
from datetime import datetime

def run_step(cmd, name):
    print(f"\n{'='*60}\n🚀 Starting: {name}\n{'='*60}")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,
            encoding='utf-8'
        )
        process.wait()
        if process.returncode != 0:
            print(f"\n❌ {name} failed with exit code {process.returncode}")
            return False
        print(f"\n✅ {name} completed successfully.")
        return True
    except Exception as e:
        print(f"\n❌ Exception in {name}: {e}")
        return False

def get_today_trends(dashboard_dir):
    trends_file = dashboard_dir / "api" / "engines" / "trend_scan" / "latest_trends.json"
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Check if we already have trends for today
    if trends_file.exists():
        try:
            with open(trends_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("date") == today_str and "lookforward_topics" in data:
                print(f"✅ Found existing trend scan for today ({today_str}).")
                return data
        except Exception as e:
            print(f"⚠️ Error reading trends file: {e}")

    # If not, run trend scan
    print("🔍 No trend scan found for today. Running Trend Scan...")
    cmd1 = [sys.executable, str(dashboard_dir / "api" / "engines" / "trend_scan" / "daily_trend_scan.py")]
    if not run_step(cmd1, "Trend Scan"):
        return None
        
    # Read newly generated file
    if trends_file.exists():
        with open(trends_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def main():
    print("🌟 STARTING FULL AUTOMATED PIPELINE 🌟")
    print("Sequence: Trend Scan (if needed) -> Lookforward -> Image Gen -> Facebook Auto Post")
    
    dashboard_dir = Path(__file__).resolve().parent.parent.parent
    
    # 1. Trend Scan & Topic Selection
    trends_data = get_today_trends(dashboard_dir)
    if not trends_data:
        print("❌ Failed to get trend data.")
        return 1
        
    topics = trends_data.get("lookforward_topics", [])
    if not topics:
        print("❌ No topics found in trend data.")
        return 1
        
    # Select rank based on time of day
    current_hour = datetime.now().hour
    if current_hour < 10:
        rank = 0  # 08:00 -> Rank 1
        rank_str = "Rank 1 (Morning)"
    elif current_hour < 16:
        rank = 1  # 12:00 -> Rank 2
        rank_str = "Rank 2 (Noon)"
    else:
        rank = 2  # 20:00 -> Rank 3
        rank_str = "Rank 3 (Evening)"
        
    # Fallback if we have fewer topics than expected
    if rank >= len(topics):
        rank = len(topics) - 1
        
    selected_topic = topics[rank]["topic"]
    print(f"\n🎯 Selected Topic: {selected_topic} [{rank_str}]")
        
    # 2. Lookforward (Strategy + Content + Prompt generation only)
    cmd2 = [
        sys.executable, 
        str(dashboard_dir / "api" / "engines" / "lookforward" / "scripts" / "run_pipeline_gemini.py"),
        selected_topic,
        "--legacy"  # Force legacy mode without --gen-images so it stops after ready_to_post
    ]
    if not run_step(cmd2, "Lookforward Content Gen"):
        return 1
        
    # 3. Image Gen
    cmd3 = [sys.executable, str(dashboard_dir / "api" / "engines" / "image_gen" / "gen_from_prompt.py")]
    if not run_step(cmd3, "Image Gen"):
        return 1
        
    # 4. Facebook Auto Post
    cmd4 = [sys.executable, str(dashboard_dir / "api" / "engines" / "social" / "facebook_poster.py")]
    if not run_step(cmd4, "Facebook Auto Poster"):
        return 1
        
    print("\n🎉 FULL PIPELINE COMPLETED SUCCESSFULLY! 🎉")
    return 0

if __name__ == "__main__":
    sys.exit(main())

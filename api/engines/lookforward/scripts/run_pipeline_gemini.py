#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lookforward Content Pipeline (Gemini Edition - THAI)
End-to-End Automation: Strategy -> Content + Visuals -> Ready-to-Post
"""

import sys
import os
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
import base64

# ==========================================
# 🛠️ COMMON SHARED LIBRARY INTEGRATION
# ==========================================

# 1. Locate engines root and add to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent  # Dashboard root
engines_dir = Path(__file__).resolve().parent.parent.parent  # Engines root
sys.path.insert(0, str(engines_dir))

# 2. Import from common
try:
    from common.utils import (
        setup_logger,
        get_date_str,
        ensure_dir,
        sanitize_filename,
        print_header,
        print_success,
        print_error,
        print_info,
        print_warning,
    )
    from common.config import Config
    from common.ai_client import create_ai_client, GeminiClient
except ImportError as e:
    print(f"❌ Failed to import common library: {e}")
    sys.exit(1)

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================


class PipelineConfig:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent
        self.workspace_root = self.project_root.parent.parent.parent  # OpenClaw root
        self.data_dir = self.workspace_root / "data" / "content" / "lookforward"
        self.paths = {
            "drafts": self.data_dir / "drafts",
            "ready_to_post": self.data_dir / "ready_to_post",
            "published": self.data_dir / "published",
            "state": self.data_dir / "state",
            "error_logs": self.data_dir / "logs",
        }


CONFIG = PipelineConfig()
ensure_dir(CONFIG.paths["error_logs"])
LOGGER = setup_logger("Pipeline", CONFIG.paths["error_logs"] / "pipeline.log")

# ==========================================
# 🚀 PIPELINE STEPS
# ==========================================


def step_1_strategy(topic, ai_client):
    print_header(f"🧠 Strategy Phase (Thai): {topic}")

    system_prompt = """คุณคือ Lead Tech Strategist ของเพจ 'lookforward'
หน้าที่ของคุณคือวิเคราะห์ Trend เทคโนโลยีและวางแผน Content Strategy ระดับผู้เชี่ยวชาญ (Insight Score 5/5)

## เป้าหมายหลัก
เจาะลึกเนื้อหาหา "คุณค่าที่แท้จริง (Real Value)" เทียบกับ "กระแส (Hype)"

## รูปแบบผลลัพธ์ (Markdown ภาษาไทย)
1. **Factual Foundation**: เกิดอะไรขึ้นกันแน่? (ใคร, ทำอะไร, ที่ไหน, สเปคเป็นยังไง)
2. **Technical Breakdown**: มันทำงานยังไงในเชิงลึก? (Architecture, Mechanism แบบเข้าใจง่ายแต่ไม่ตื้น)
3. **Non-Obvious Angle**: มุมมองที่คนส่วนใหญ่มองข้ามคืออะไร?
4. **Impact Analysis**: ใครได้ประโยชน์? ใครเสียประโยชน์? (มองภาพรวมระบบ)
5. **Future Vision**: ในอีก 6-12 เดือนข้างหน้า มันจะไปทางไหน?
6. **Content Angle**:
   - Hook: ประโยคเปิดที่ชวนสงสัยและหักมุมความเชื่อเดิม
   - Key Message: สรุปใจความสำคัญในประโยคเดียว
   - Tone: มืออาชีพ (Professional), เฉียบคม (Sharp), มีวิสัยทัศน์ (Visionary)
"""
    user_prompt = f"ช่วยวิเคราะห์หัวข้อนี้สำหรับเขียนโพสต์ Tech Authority เป็นภาษาไทย: {topic}"

    # Use Shared AI Client
    response = ai_client.generate(user_prompt, system=system_prompt)

    if response:
        print_success("Strategy Generated Successfully! (Thai)")
        return response
    else:
        print_error("Failed to generate strategy.")
        return None


def step_2_content(topic, strategy, ai_client):
    print_header(f"✍️ Writing Phase (Thai): {topic}")

    system_prompt = """คุณคือ Lead Tech Writer ของเพจ 'lookforward'
หน้าที่ของคุณคือเขียนบทความ Tech Analysis เชิงลึก ภาษาไทย ตาม Strategy ที่ได้รับมอบหมาย

## แนวทางการเขียน (Strict Guidelines)
- **ภาษาไทย**: ใช้ภาษาไทยเป็นหลัก ทับศัพท์ภาษาอังกฤษเฉพาะคำเทคนิคที่จำเป็น (Tech Terms) เพื่อความลื่นไหลและดูเป็นธรรมชาติ
- **Insight Score 5/5**: ต้องมีการวิเคราะห์เชิงระบบ ไม่ใช่แค่รายงานข่าว
- **Structure**:
  1. **Hook**: เปิดด้วยความจริงที่น่าตกใจ หรือมุมมองที่สวนกระแส (ไม่ต้องมีคำนำว่า "สวัสดีครับ")
  2. **The Context**: สรุปสิ่งที่เกิดขึ้นสั้นๆ
  3. **The Mechanism**: อธิบายการทำงานเชิงลึก (How it works)
  4. **The Analysis**: วิเคราะห์ผลกระทบ (Winners/Losers)
  5. **The Vision**: อนาคตจะเป็นอย่างไร
  6. **Final Thought**: บทสรุปปิดท้ายที่เฉียบคม

## Output JSON Format ONLY
ต้องส่งคืนเป็น JSON Object เท่านั้น:
{
  "content": {
    "text": "เนื้อหาบทความเต็มรูปแบบ (Markdown)...",
    "insight_score": 5,
    "char_count": 0
  },
  "caption": "แคปชั่นสั้นๆ สำหรับโพสต์ Facebook (เน้น Hook ให้น่ากดอ่านต่อ)",
  "hashtags": ["#Tag1", "#Tag2", "#lookforward"],
  "image_prompts": [
    {"title": "Visual 1", "prompt": "Detailed prompt for technical diagram..."},
    {"title": "Visual 2", "prompt": "Detailed prompt for abstract concept..."}
  ]
}
"""
    user_prompt = f"หัวข้อ: {topic}\n\nกลยุทธ์การวิเคราะห์:\n{strategy}\n\nเขียนบทความฉบับสมบูรณ์เป็น JSON ภาษาไทย:"

    # Use json_mode=True for guaranteed valid JSON from Gemini
    raw_response = ai_client.generate(user_prompt, system=system_prompt, json_mode=True)
    if not raw_response:
        print_error("Failed to generate content.")
        return None

    # Extract and parse JSON
    try:
        # Cleanup response string (Gemini sometimes adds markdown even in JSON mode)
        json_str = raw_response.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif json_str.startswith("```"):
            json_str = json_str.split("```")[1].split("```")[0].strip()

        data = json.loads(json_str)

        # Calculate char count
        if "content" in data and "text" in data["content"]:
            data["content"]["char_count"] = len(data["content"]["text"])

        print_success("Content Generated Successfully! (Thai)")
        return data
    except json.JSONDecodeError as e:
        print_error(f"Failed to parse JSON content: {e}")
        # print_info(f"Raw response: {raw_response[:200]}...") # Optional debug
        return None


def step_3_images(image_prompts, ai_client):
    if not image_prompts:
        return []

    print_header(f"🖼️ Visual Gen Phase: {len(image_prompts)} Images")

    generated_images = []
    for i, img_prompt in enumerate(image_prompts, 1):
        prompt = img_prompt.get("prompt")
        title = img_prompt.get("title", f"Image {i}")

        print(f"   Generating: {title}...")
        try:
            # Use HuggingFace FLUX.1 [schnell] for free image generation
            from huggingface_hub import InferenceClient

            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                client = InferenceClient(provider="auto", api_key=hf_token)
                image = client.text_to_image(
                    prompt, model="black-forest-labs/FLUX.1-schnell"
                )

                # Convert PIL image to base64
                import io

                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                image_b64 = base64.b64encode(buffered.getvalue()).decode()

                generated_images.append(
                    {"title": title, "mime_type": "image/png", "data_b64": image_b64}
                )
                print_success(f"   ✅ Generated via HuggingFace: {title}")
            else:
                # Fallback to shared client if HF_TOKEN not set
                image_b64 = ai_client.generate_image(prompt)
                if image_b64:
                    generated_images.append(
                        {
                            "title": title,
                            "mime_type": "image/png",
                            "data_b64": image_b64,
                        }
                    )
                    print_success(f"   ✅ Generated: {title}")
                else:
                    print_error(f"   ❌ Failed to generate: {title}")
        except Exception as e:
            print_error(f"   ❌ Error generating {title}: {e}")

    return generated_images


def create_ready_to_post(topic, content_data, images):
    """
    Create a ready-to-post package in 09_ReadyToPost.
    """
    date_str = get_date_str()
    ready_dir = CONFIG.paths["ready_to_post"]

    ready_dir = ready_dir / date_str

    # Create topic specific folder
    safe_topic = sanitize_filename(topic, max_length=50)  # use shared util
    timestamp = datetime.now().strftime("%H%M%S")
    post_dir = ready_dir / f"{safe_topic}_{timestamp}"
    ensure_dir(post_dir)

    print_header(f"📦 Creating Ready-to-Post Package: {post_dir.name}")

    # Extract clean content
    body_text = content_data["content"].get("text", "")
    caption = content_data.get("caption", "")
    hashtags = " ".join(content_data.get("hashtags", []))

    # 1. post.txt
    post_content = f"{body_text}\n\n{hashtags}"
    with open(post_dir / "post.txt", "w", encoding="utf-8") as f:
        f.write(post_content)
    print_success(" ✅ post.txt - Ready to copy!")

    # 2. caption.txt
    with open(post_dir / "caption.txt", "w", encoding="utf-8") as f:
        f.write(caption)
    print_success(" ✅ caption.txt")

    # 3. hashtags.txt
    with open(post_dir / "hashtags.txt", "w", encoding="utf-8") as f:
        f.write(hashtags)
    print_success(" ✅ hashtags.txt")

    # 4. media/
    media_dir = post_dir / "media"
    ensure_dir(media_dir)
    if images:
        import base64

        for i, img in enumerate(images, 1):
            ext = img.get("mime_type", "image/png").split("/")[-1]
            fname = f"image_{i}.{ext}"
            with open(media_dir / fname, "wb") as f:
                f.write(base64.b64decode(img["data_b64"]))
            print_success(f" ✅ media/{fname}")
    else:
        # Create prompts helper if no images
        prompts_helper = "AI Studio Image Prompts:\n\n"
        for i, img in enumerate(content_data.get("image_prompts", []), 1):
            prompts_helper += f"Image {i}: {img.get('prompt')}\n\n"
        with open(media_dir / "prompts_guide.txt", "w", encoding="utf-8") as f:
            f.write(prompts_helper)
        print_info(" ✅ media/prompts_guide.txt created.")

    # 5. _metadata.json
    metadata = {
        "topic": topic,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "insight_score": content_data["content"].get("insight_score", "?"),
    }
    with open(post_dir / "_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print_success(f"\n🚀 READY TO POST: {post_dir}")
    print_info("   1. Open post.txt → Copy content")
    print_info("   2. Upload images (AI Studio)")
    print_info("   3. Post!")

    return post_dir


def save_final_package(topic, strategy, content_data, images):
    """Save to Drafts."""
    date_str = get_date_str()
    draft_dir = CONFIG.paths["drafts"] / date_str

    safe_topic = sanitize_filename(topic, max_length=50)
    timestamp = datetime.now().strftime("%H%M%S")
    package_dir = draft_dir / f"{safe_topic}_{timestamp}"
    ensure_dir(package_dir)

    print_header(f"💾 Saving Draft Package: {package_dir}")

    # Save Strategy
    with open(package_dir / "01_strategy.md", "w", encoding="utf-8") as f:
        f.write(f"# Strategy: {topic}\n\n{strategy}")

    # Save Content
    with open(package_dir / "02_content.json", "w", encoding="utf-8") as f:
        json.dump(content_data, f, indent=2, ensure_ascii=False)

    md_content = f"""# {topic}
**Generated**: {datetime.now()}
**Insight Score**: {content_data["content"].get("insight_score", "?")}/5
---
{content_data["content"].get("text", "")}
---
**Caption**: {content_data.get("caption", "")}
**Hashtags**: {" ".join(content_data.get("hashtags", []))}
"""
    with open(package_dir / "02_content.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    # Save Prompts
    prompts_text = ""
    for i, img in enumerate(content_data.get("image_prompts", []), 1):
        prompts_text += f"### Image {i}: {img.get('title')}\n{img.get('prompt')}\n\n"

    with open(package_dir / "03_visual_prompts.md", "w", encoding="utf-8") as f:
        f.write(prompts_text)

    print_success(f"✅ Draft saved: {package_dir.name}")
    return package_dir


# ==========================================
# 🏁 MAIN EXECUTION (Upgraded with Pipeline Controller)
# ==========================================


def main():
    """
    Main entry point with upgraded pipeline options.

    Supports both legacy mode (backward compatible) and new pipeline modes.

    Legacy mode:
        python run_pipeline_gemini.py "Topic" --gen-images

    New mode (recommended):
        python run_pipeline_gemini.py "Topic" --mode quick
        python run_pipeline_gemini.py "Topic" --mode full --gen-images
        python run_pipeline_gemini.py --resume-from content
        python run_pipeline_gemini.py "Topic" --dry-run
    """
    parser = argparse.ArgumentParser(
        description="Run Full Content Pipeline (Thai Edition) - Upgraded",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Legacy mode (backward compatible)
  python run_pipeline_gemini.py "AI Trends 2026" --gen-images
  
  # New mode - Quick (no images)
  python run_pipeline_gemini.py "AI Trends 2026" --mode quick
  
  # New mode - Full with images
  python run_pipeline_gemini.py "AI Trends 2026" --mode full --gen-images
  
  # Strategy only
  python run_pipeline_gemini.py "AI Trends 2026" --mode strategy-only
  
  # Resume from failed step
  python run_pipeline_gemini.py --resume-from content
  
  # Dry run (preview)
  python run_pipeline_gemini.py "AI Trends 2026" --dry-run
  
  # Check status
  python run_pipeline_gemini.py --status
        """,
    )

    parser.add_argument("topic", nargs="?", help="Topic to process (Thai or English)")

    # Legacy option (backward compatible)
    parser.add_argument(
        "--gen-images",
        action="store_true",
        help="Enable image generation (Default: False)",
    )

    # New options
    parser.add_argument(
        "--mode",
        choices=["full", "quick", "strategy-only", "content-only"],
        default=None,
        help="Pipeline mode: full (all steps), quick (skip images), strategy-only, content-only",
    )

    parser.add_argument(
        "--resume-from",
        metavar="STEP",
        help="Resume from a specific step (strategy, content, images, ready_to_post)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview pipeline without executing"
    )

    parser.add_argument(
        "--status", action="store_true", help="Show current pipeline status"
    )

    parser.add_argument(
        "--history", action="store_true", help="Show pipeline run history"
    )

    parser.add_argument(
        "--tone",
        choices=["professional", "casual", "educational"],
        default="professional",
        help="Content tone: professional, casual, educational",
    )

    parser.add_argument(
        "--max-words", type=int, default=800, help="Maximum word count for content"
    )

    parser.add_argument(
        "--no-images", action="store_true", help="Disable image generation"
    )

    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy pipeline (backward compatible mode)",
    )

    args = parser.parse_args()

    # Determine if using new pipeline controller or legacy mode
    use_new_pipeline = (
        args.mode is not None
        or args.resume_from is not None
        or args.dry_run
        or args.status
        or args.history
    )

    if use_new_pipeline and not args.legacy:
        # Use new pipeline controller
        from pipeline_controller import LookforwardPipeline

        pipeline = LookforwardPipeline()

        # Handle status command
        if args.status:
            progress = pipeline.get_progress()
            print_header("Pipeline Status")
            print(f"  Run ID: {progress.get('run_id', 'None')}")
            print(f"  Status: {progress.get('status', 'idle')}")
            print(f"  Current Step: {progress.get('current_step', 'None')}")
            print(f"  Progress: {progress.get('progress_percent', 0)}%")
            return

        # Handle history command
        if args.history:
            history = pipeline.get_history(limit=5)
            print_header("Pipeline History")
            for run in history:
                print(
                    f"  {run.get('run_id')}: {run.get('status')} - {run.get('topic', 'N/A')}"
                )
            return

        # Handle resume
        if args.resume_from:
            valid_steps = ["strategy", "content", "images", "ready_to_post"]
            if args.resume_from not in valid_steps:
                print_error(f"Invalid step: {args.resume_from}")
                print_info(f"Valid steps: {valid_steps}")
                sys.exit(1)

            result = pipeline.run(topic="", mode="resume", resume_from=args.resume_from)
            sys.exit(0 if result.get("success") else 1)

        # Require topic for normal run
        if not args.topic:
            parser.print_help()
            return

        # Build options
        options = {"gen_images": args.gen_images, "dry_run": args.dry_run}

        # Determine mode
        mode = args.mode or ("full" if args.gen_images else "quick")

        # Run pipeline
        result = pipeline.run(topic=args.topic, mode=mode, options=options)

        sys.exit(0 if result.get("success") else 1)

    else:
        # Legacy mode (backward compatible)
        if not args.topic:
            parser.print_help()
            return

        print_info("Running in legacy mode (use --mode for new pipeline features)")

        # Initialize Shared AI Client
        ai_client = create_ai_client(LOGGER)
        if not ai_client:
            sys.exit(1)

        # 1. Strategy
        strategy = step_1_strategy(args.topic, ai_client)
        if not strategy:
            sys.exit(1)

        # 2. Content & Prompts
        content_data = step_2_content(args.topic, strategy, ai_client)
        if not content_data:
            sys.exit(1)

        # 3. Images
        images = []
        if args.gen_images:
            images = step_3_images(content_data.get("image_prompts", []), ai_client)
        else:
            # Create empty media folder by default
            print_info("Skipping image generation (Use --gen-images to enable).")

        # 4. Save Draft Package (Full details)
        save_final_package(args.topic, strategy, content_data, images)

        # 5. Create Ready-to-Post Package (Clean files)
        create_ready_to_post(args.topic, content_data, images)

        print_header("✅ WORKFLOW COMPLETE!")

        sys.exit(0)


if __name__ == "__main__":
    main()

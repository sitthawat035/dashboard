# =============================================================================
# batch_runner.py — Batch Video Generation via Google Flow Labs
# =============================================================================
# รันหลายรูปสินค้าต่อเนื่อง ดึง prompt จาก veo_gen engine อัตโนมัติ
# Usage:
#   python batch_runner.py --image-dir ./products/
#   python batch_runner.py --image-list products.txt --delay 60
#   python batch_runner.py --image img1.jpg img2.jpg img3.jpg
# =============================================================================

import os
import sys
import json
import time
import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List

SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from veo_automator import VeoAutomator

# Output base
OUTPUT_BASE = SCRIPT_DIR.parent.parent / "data" / "content" / "veo_output"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("batch_runner")

# =============================================================================
# Image Collection
# =============================================================================

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def collect_images(args) -> List[Path]:
    """Collect image paths from various input methods."""
    images = []

    # Method 1: Explicit image list
    if args.image:
        for img in args.image:
            p = Path(img)
            if p.exists() and p.suffix.lower() in IMAGE_EXTENSIONS:
                images.append(p)
            else:
                log.warning(f"⚠️ Skipping invalid image: {img}")

    # Method 2: Directory scan
    if args.image_dir:
        img_dir = Path(args.image_dir)
        if img_dir.is_dir():
            for f in sorted(img_dir.iterdir()):
                if f.suffix.lower() in IMAGE_EXTENSIONS:
                    images.append(f)
            log.info(f"📁 Found {len(images)} images in {img_dir}")
        else:
            log.error(f"❌ Directory not found: {img_dir}")

    # Method 3: List file (one path per line)
    if args.image_list:
        list_file = Path(args.image_list)
        if list_file.exists():
            with open(list_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        p = Path(line)
                        if p.exists() and p.suffix.lower() in IMAGE_EXTENSIONS:
                            images.append(p)
                        else:
                            log.warning(f"⚠️ Skipping: {line}")
            log.info(f"📋 Loaded {len(images)} images from {list_file}")
        else:
            log.error(f"❌ List file not found: {list_file}")

    # Deduplicate
    seen = set()
    unique = []
    for img in images:
        resolved = img.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(img)

    return unique


# =============================================================================
# Prompt Generator
# =============================================================================

def generate_prompts_for_image(image_path: str) -> dict:
    """Call manual_veo.py engine to generate prompts for a product image."""
    from manual_veo import generate_prompts
    return generate_prompts(image_path)


# =============================================================================
# Batch Runner
# =============================================================================

async def run_batch(
    images: List[Path],
    delay: int = 45,
    cdp_port: int = 9222,
    skip_keyframe: bool = False,
    dry_run: bool = False,
):
    """Process multiple images through the full pipeline."""
    total = len(images)
    batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = OUTPUT_BASE / f"batch_{batch_timestamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    log.info("=" * 60)
    log.info(f"🚀 BATCH RUN: {total} image(s)")
    log.info(f"   Output: {batch_dir}")
    log.info(f"   Delay between items: {delay}s")
    log.info(f"   Dry run: {dry_run}")
    log.info("=" * 60)

    results = []
    success_count = 0
    fail_count = 0

    for idx, image_path in enumerate(images, 1):
        log.info("")
        log.info(f"━━━ [{idx}/{total}] {image_path.name} ━━━")

        item_result = {
            "index": idx,
            "image": str(image_path),
            "status": "pending",
            "prompts": None,
            "output": None,
            "error": None,
        }

        try:
            # Generate prompts
            log.info("🤖 Generating prompts...")
            prompts = generate_prompts_for_image(str(image_path))
            if not prompts:
                item_result["status"] = "error"
                item_result["error"] = "Failed to generate prompts"
                fail_count += 1
                results.append(item_result)
                continue

            item_result["prompts"] = prompts

            if dry_run:
                log.info("🏃 DRY RUN — skipping automation")
                item_result["status"] = "dry_run"
                results.append(item_result)
                continue

            # Create per-item output directory
            item_dir = batch_dir / f"{idx:02d}_{image_path.stem}"

            # Run automation
            automator = VeoAutomator(output_dir=item_dir)

            if not await automator.connect():
                item_result["status"] = "error"
                item_result["error"] = "CDP connection failed"
                fail_count += 1
                results.append(item_result)
                continue

            try:
                pipeline_result = await automator.run_full_pipeline(
                    image_path=str(image_path),
                    prompts=prompts,
                    skip_keyframe=skip_keyframe,
                )
                item_result["output"] = pipeline_result

                if pipeline_result["success"]:
                    item_result["status"] = "success"
                    success_count += 1
                else:
                    item_result["status"] = "partial"
                    fail_count += 1

            finally:
                await automator.close()

        except Exception as e:
            item_result["status"] = "error"
            item_result["error"] = str(e)
            fail_count += 1
            log.error(f"❌ Error processing {image_path.name}: {e}")

        results.append(item_result)

        # Delay between items (skip after last)
        if idx < total:
            log.info(f"⏳ Waiting {delay}s before next item (rate limit buffer)...")
            await asyncio.sleep(delay)

    # =================================================================
    # Batch Summary
    # =================================================================
    log.info("")
    log.info("=" * 60)
    log.info("📊 BATCH SUMMARY")
    log.info("=" * 60)
    log.info(f"   Total:   {total}")
    log.info(f"   Success: {success_count}")
    log.info(f"   Failed:  {fail_count}")
    log.info(f"   Output:  {batch_dir}")
    log.info("=" * 60)

    # Save batch report
    report = {
        "batch_id": batch_timestamp,
        "total": total,
        "success": success_count,
        "failed": fail_count,
        "items": results,
    }
    report_path = batch_dir / "batch_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    log.info(f"📝 Report saved: {report_path}")

    return report


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Batch Video Generation — Google Flow Labs Automation"
    )
    parser.add_argument(
        "--image", nargs="+",
        help="One or more image paths"
    )
    parser.add_argument(
        "--image-dir",
        help="Directory containing product images"
    )
    parser.add_argument(
        "--image-list",
        help="Text file with image paths (one per line)"
    )
    parser.add_argument(
        "--delay", type=int, default=45,
        help="Delay (seconds) between each generation (default: 45)"
    )
    parser.add_argument(
        "--cdp-port", type=int, default=9222,
        help="Chrome CDP port (default: 9222)"
    )
    parser.add_argument(
        "--skip-keyframe", action="store_true",
        help="Skip STEP 1 (keyframe generation), go straight to video"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Generate prompts only, don't automate browser"
    )
    args = parser.parse_args()

    # Collect images
    images = collect_images(args)
    if not images:
        print("❌ ไม่พบรูปภาพ — ต้องระบุ --image, --image-dir, หรือ --image-list")
        parser.print_help()
        sys.exit(1)

    print(f"📸 Found {len(images)} image(s):")
    for img in images:
        print(f"   • {img}")

    # Run batch
    report = asyncio.run(run_batch(
        images=images,
        delay=args.delay,
        cdp_port=args.cdp_port,
        skip_keyframe=args.skip_keyframe,
        dry_run=args.dry_run,
    ))

    # Print final JSON result
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()

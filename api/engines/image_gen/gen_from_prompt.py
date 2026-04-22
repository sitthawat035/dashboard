#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image Gen Engine
Reads image prompts from a Lookforward ready_to_post package and generates
images using HuggingFace FLUX.1-schnell, saving them into media/.

Usage:
  python gen_from_prompt.py                          # auto-detect latest package
  python gen_from_prompt.py --package-path <path>   # specific package
  python gen_from_prompt.py --num-images 2           # limit number of images
  python gen_from_prompt.py --model FLUX.1-dev       # alternative model
"""

import sys
import os
import io
import json
import argparse
from pathlib import Path
from datetime import datetime

# ── Locate engines root and inject common into path ─────────────────────────
engines_dir = Path(__file__).resolve().parent.parent  # api/engines/
sys.path.insert(0, str(engines_dir))

try:
    from common.utils import setup_logger, ensure_dir, print_header, print_success, print_error, print_info
    from common.config import Config
except ImportError as e:
    print(f"❌ Failed to import common library: {e}")
    sys.exit(1)

from dotenv import load_dotenv

# ── Config ───────────────────────────────────────────────────────────────────
dashboard_dir = Path(__file__).resolve().parent.parent.parent.parent  # dashboard root
load_dotenv(dashboard_dir / ".env")

READY_TO_POST_BASE = dashboard_dir / "data" / "content" / "lookforward" / "ready_to_post"

SUPPORTED_MODELS = {
    "FLUX.1-schnell": "black-forest-labs/FLUX.1-schnell",
    "FLUX.1-dev":     "black-forest-labs/FLUX.1-dev",
}

logger = setup_logger("ImageGen", dashboard_dir / "data" / "logs" / "image_gen.log")


def find_latest_package() -> Path | None:
    """Auto-detect the most recently modified ready_to_post package."""
    if not READY_TO_POST_BASE.exists():
        return None

    # Walk date folders (YYYY-MM-DD) newest first
    date_folders = sorted(
        [d for d in READY_TO_POST_BASE.iterdir() if d.is_dir() and d.name.startswith("20")],
        reverse=True,
    )
    for date_folder in date_folders:
        packages = sorted(
            [d for d in date_folder.iterdir() if d.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if packages:
            return packages[0]
    return None


def load_prompts(package_path: Path) -> list[dict]:
    """
    Load image prompts from a package directory.
    Checks (in order):
      1. _metadata.json -> image_prompts key (if Lookforward saved them there)
      2. content data file (02_content.json) -> image_prompts
      3. media/prompts_guide.txt  -> parse plain text prompts
    """
    # 1. Try content JSON first
    content_json = package_path / "02_content.json"
    if content_json.exists():
        try:
            with open(content_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            prompts = data.get("image_prompts", [])
            if prompts:
                print_info(f"📄 Loaded {len(prompts)} prompt(s) from 02_content.json")
                return prompts
        except Exception:
            pass

    # 2. Try prompts_guide.txt (fallback)
    prompts_txt = package_path / "media" / "prompts_guide.txt"
    if prompts_txt.exists():
        prompts = []
        with open(prompts_txt, "r", encoding="utf-8") as f:
            content = f.read()
        # Parse "Image N: <prompt>" pattern
        import re
        matches = re.findall(r"Image\s+\d+:\s*(.+?)(?=Image\s+\d+:|$)", content, re.DOTALL)
        for i, match in enumerate(matches, 1):
            prompt_text = match.strip()
            if prompt_text:
                prompts.append({"title": f"Image {i}", "prompt": prompt_text})
        if prompts:
            print_info(f"📄 Loaded {len(prompts)} prompt(s) from prompts_guide.txt")
            return prompts

    return []


def generate_image_hf(prompt: str, model_id: str, hf_token: str) -> bytes | None:
    """Generate an image via HuggingFace Inference API, return raw PNG bytes."""
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(provider="auto", api_key=hf_token)
        pil_image = client.text_to_image(prompt, model=model_id)
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        print_error(f"   HuggingFace generation failed: {e}")
        return None


def run(package_path: Path, model_key: str, num_images: int) -> bool:
    """
    Main logic: generate images for one package.
    Returns True on full success, False on any error.
    """
    print_header(f"🖼️  Image Gen Engine — {package_path.name}")

    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print_error("❌ HF_TOKEN not set in .env — cannot generate images.")
        return False

    model_id = SUPPORTED_MODELS.get(model_key, SUPPORTED_MODELS["FLUX.1-schnell"])
    print_info(f"Model  : {model_key} ({model_id})")
    print_info(f"Package: {package_path}")

    prompts = load_prompts(package_path)
    if not prompts:
        print_error("❌ No image prompts found in this package.")
        return False

    # Respect num_images cap
    prompts = prompts[:num_images]
    print_info(f"Generating {len(prompts)} image(s)...")

    media_dir = package_path / "media"
    ensure_dir(media_dir)

    success_count = 0
    for i, item in enumerate(prompts, 1):
        title = item.get("title", f"Image {i}")
        prompt = item.get("prompt", "")
        if not prompt:
            print_error(f"   ⚠️ Skipping empty prompt for: {title}")
            continue

        print_info(f"   [{i}/{len(prompts)}] {title}...")
        image_bytes = generate_image_hf(prompt, model_id, hf_token)
        if image_bytes:
            out_path = media_dir / f"image_{i}.png"
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            print_success(f"   ✅ Saved: media/image_{i}.png ({len(image_bytes) // 1024} KB)")
            success_count += 1
        else:
            print_error(f"   ❌ Failed to generate: {title}")

    # Remove placeholder prompts_guide.txt if we successfully generated images
    guide_file = media_dir / "prompts_guide.txt"
    if success_count > 0 and guide_file.exists():
        guide_file.unlink()

    # Update metadata
    meta_path = package_path / "_metadata.json"
    try:
        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        meta["images_generated"] = success_count
        meta["image_gen_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta["model"] = model_key
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    if success_count == len(prompts):
        print_success(f"\n✅ All {success_count} image(s) generated successfully!")
        return True
    elif success_count > 0:
        print_info(f"\n⚠️ Partial success: {success_count}/{len(prompts)} images generated.")
        return True
    else:
        print_error("\n❌ All generations failed.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Image Gen Engine — Generate images from Lookforward prompts"
    )
    parser.add_argument(
        "--package-path",
        help="Path to ready_to_post package (default: auto-detect latest)",
    )
    parser.add_argument(
        "--model",
        choices=list(SUPPORTED_MODELS.keys()),
        default="FLUX.1-schnell",
        help="HuggingFace model to use (default: FLUX.1-schnell)",
    )
    parser.add_argument(
        "--num-images",
        type=int,
        default=4,
        help="Max number of images to generate (default: 4)",
    )
    args = parser.parse_args()

    # Resolve package path
    if args.package_path:
        package = Path(args.package_path)
        if not package.exists():
            print_error(f"❌ Package path not found: {package}")
            sys.exit(1)
    else:
        print_info("🔍 Auto-detecting latest ready_to_post package...")
        package = find_latest_package()
        if not package:
            print_error(f"❌ No ready_to_post packages found in:\n   {READY_TO_POST_BASE}")
            sys.exit(1)
        print_success(f"✅ Found: {package}")

    success = run(package, args.model, args.num_images)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

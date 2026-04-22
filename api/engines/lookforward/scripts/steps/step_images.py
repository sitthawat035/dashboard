"""
Images Step for Lookforward Pipeline
=====================================

Image Generation Priority:
  1. Pollinations.ai — ฟรี 100%, ไม่ต้อง API key, Flux model
  2. Gemini API     — ถ้ามี GEMINI_API_KEY (จำกัด 25 RPD free tier)
  3. prompts_guide.txt — fallback เสมอ (copy ไป AI Studio / Midjourney)
"""

import os
import sys
import base64
import json
import time
import random
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import quote

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent
sys.path.insert(0, str(root_dir))

from .base_step import BaseLookforwardStep, StepResult
from common.utils import print_header, print_success, print_error, print_info


# ─── Style Templates (wrapped around AI concept prompts) ────────────────────

STYLE_LANDSCAPE = (
    "high-end commercial photography, ultra-realistic, 16:9 widescreen, "
    "clean modern aesthetic, soft studio lighting, professional depth of field, "
    "premium editorial tech look, 8K resolution, no text, no watermarks, no logos"
)

STYLE_PORTRAIT = (
    "premium 3D abstract visualization, clean minimalism, soft gradients, "
    "9:16 portrait format, high-end editorial tech background, "
    "no readable text, no watermarks, no logos, ample space for text overlay"
)

STYLE_INFOGRAPHIC = (
    "clean minimal vector illustration, flat design, modern UI/UX aesthetic, "
    "light background, elegant data visualization concept, no photographs"
)

FORMAT_CONFIG = {
    "landscape": {"style": STYLE_LANDSCAPE, "width": 1280, "height": 720},
    "portrait":  {"style": STYLE_PORTRAIT,  "width": 720,  "height": 1280},
    "infographic": {"style": STYLE_INFOGRAPHIC, "width": 1024, "height": 1024},
    "square":    {"style": STYLE_LANDSCAPE, "width": 1024, "height": 1024},
}


class StepImages(BaseLookforwardStep):
    """
    Image generation step.

    Uses Pollinations.ai (free, no key) as primary source.
    Falls back to Gemini API if GEMINI_API_KEY is set.
    Always saves prompts_guide.txt for manual generation.
    """

    POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

    def __init__(self):
        super().__init__("images")

    def execute(self, context: Dict[str, Any], **kwargs) -> StepResult:
        options = context.get("options", {})
        gen_images = options.get("gen_images", kwargs.get("gen_images", True))  # default ON now

        # Get content data from previous step
        step_results = context.get("step_results", {})
        content_data = step_results.get("content", {}).get("output_data", {})
        topic = context.get("topic", "lookforward")
        image_prompts = content_data.get("image_prompts", [])

        if not image_prompts:
            image_prompts = self._default_prompts(topic)

        # Setup dirs
        output_dir = self.get_output_dir(context)
        media_dir = output_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        # Enhance prompts
        enhanced = [self._enhance_prompt(p) for p in image_prompts]

        # Always save guide
        self._save_prompts_guide(media_dir, enhanced, topic)

        if not gen_images:
            print_info("Image generation skipped (gen_images=False)")
            print_info(f"Prompts guide -> {media_dir}/prompts_guide.txt")
            return StepResult(
                success=True,
                output_data={
                    "images": [], "skipped": True,
                    "prompts_file": str(media_dir / "prompts_guide.txt"),
                }
            )

        print_header(f"Visual Gen: {len(enhanced)} images")

        hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
        if hf_token:
            print_info("Using HuggingFace FLUX.1-schnell (primary)")
        else:
            print_info("Using Pollinations.ai (primary)")

        generated = []
        for i, img in enumerate(enhanced, 1):
            title = img.get("title", f"Image {i}")
            print(f"\n   [{i}/{len(enhanced)}] {title}")

            result = None

            # Priority 1: HuggingFace FLUX.1
            if hf_token:
                result = self._generate_huggingface(img, i, title, media_dir, hf_token)

            # Priority 2: Pollinations.ai
            if not result:
                if hf_token:
                    print_info("   HF failed - trying Pollinations.ai...")
                result = self._generate_pollinations(img, i, title, media_dir)

            # Priority 3: Gemini API
            if not result and os.getenv("GEMINI_API_KEY"):
                print_info("   Pollinations failed - trying Gemini API...")
                result = self._generate_gemini(img, i, title, media_dir)

            if result:
                generated.append(result)
                src = result.get("source", "?")
                print_success(f"   [{src}] Saved: {Path(result['path']).name} ({result.get('size_kb', '?')} KB)")
            else:
                print_error(f"   All sources failed")

        print_success(f"\nGenerated {len(generated)}/{len(enhanced)} images -> {media_dir}")

        return StepResult(
            success=True,
            output_data={
                "images": generated,
                "prompts_file": str(media_dir / "prompts_guide.txt"),
                "total_generated": len(generated),
                "total_requested": len(enhanced),
                "media_dir": str(media_dir),
            }
        )

    # ─── HuggingFace FLUX.1-schnell ──────────────────────────────────────────

    def _generate_huggingface(self, img: dict, idx: int, title: str, media_dir: Path, hf_token: str) -> Optional[dict]:
        """
        Generate via HuggingFace FLUX.1-schnell (router.huggingface.co).
        ต้องมี HF_TOKEN — ฟรี สมัครที่ huggingface.co
        """
        prompt = img.get("enhanced_prompt", img.get("prompt", ""))
        url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": prompt,
            "parameters": {"num_inference_steps": 4},
        }

        for attempt in range(1, 4):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=120)

                if resp.status_code == 503:
                    body = {}
                    try:
                        body = resp.json()
                    except Exception:
                        pass
                    wait = body.get("estimated_time", 20)
                    self.logger.info(f"HF model loading — waiting {min(wait, 30):.0f}s")
                    time.sleep(min(wait, 30))
                    continue

                if resp.status_code != 200:
                    self.logger.warning(f"HF HTTP {resp.status_code}: {resp.text[:200]}")
                    return None

                ct = resp.headers.get("content-type", "")
                if "image" not in ct:
                    self.logger.warning(f"HF non-image response: {ct}")
                    return None

                ext = "jpg" if "jpeg" in ct else "png"
                safe = "".join(c if c.isalnum() or c == "_" else "_" for c in title.lower())
                fname = f"{idx:02d}_{safe}.{ext}"
                fpath = media_dir / fname
                fpath.write_bytes(resp.content)

                return {
                    "title": title,
                    "path": str(fpath),
                    "format": img.get("format", "landscape"),
                    "size_kb": round(len(resp.content) / 1024, 1),
                    "source": "huggingface",
                    "mime_type": f"image/{ext}",
                }

            except requests.exceptions.Timeout:
                self.logger.warning(f"HF timeout attempt {attempt}")
                continue
            except Exception as e:
                self.logger.warning(f"HF error: {e}")
                return None

        return None

    # ─── Pollinations.ai ────────────────────────────────────────────────────

    def _generate_pollinations(self, img: dict, idx: int, title: str, media_dir: Path) -> Optional[dict]:
        """
        Generate image via Pollinations.ai — completely free, no key needed.
        GET https://image.pollinations.ai/prompt/{prompt}?width=W&height=H&model=flux&nologo=true
        """
        prompt = img.get("enhanced_prompt", img.get("prompt", ""))
        fmt = img.get("format", "landscape").lower()
        cfg = FORMAT_CONFIG.get(fmt, FORMAT_CONFIG["landscape"])

        seed = random.randint(1, 999999)
        encoded = quote(prompt, safe="")
        url = (
            f"{self.POLLINATIONS_BASE}/{encoded}"
            f"?width={cfg['width']}&height={cfg['height']}"
            f"&model=flux&nologo=true&seed={seed}"
        )

        try:
            resp = requests.get(url, timeout=90, stream=True)
            if resp.status_code != 200:
                self.logger.warning(f"Pollinations HTTP {resp.status_code}")
                return None

            content_type = resp.headers.get("content-type", "image/jpeg")
            if "image" not in content_type:
                self.logger.warning(f"Pollinations returned non-image: {content_type}")
                return None

            ext = "jpg" if "jpeg" in content_type else "png"
            safe = "".join(c if c.isalnum() or c == "_" else "_" for c in title.lower())
            fname = f"{idx:02d}_{safe}.{ext}"
            fpath = media_dir / fname

            img_bytes = resp.content
            fpath.write_bytes(img_bytes)

            return {
                "title": title,
                "path": str(fpath),
                "format": fmt,
                "size_kb": round(len(img_bytes) / 1024, 1),
                "source": "pollinations",
                "mime_type": f"image/{ext}",
            }

        except requests.exceptions.Timeout:
            self.logger.warning("Pollinations timeout (90s)")
            return None
        except Exception as e:
            self.logger.warning(f"Pollinations error: {e}")
            return None

    # ─── Gemini Image Generation ─────────────────────────────────────────────

    def _generate_gemini(self, img: dict, idx: int, title: str, media_dir: Path) -> Optional[dict]:
        """
        Generate image via Gemini API (requires GEMINI_API_KEY).
        Model: gemini-2.0-flash-exp-image-generation
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        prompt = img.get("enhanced_prompt", img.get("prompt", ""))
        model = "gemini-2.0-flash-exp-image-generation"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": 1.0,
            }
        }

        try:
            resp = requests.post(url, json=payload, timeout=90)
            if resp.status_code != 200:
                err = resp.json().get("error", {}).get("message", resp.text)
                self.logger.warning(f"Gemini image error: {err}")
                return None

            result = resp.json()
            parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            image_data = next((p["inlineData"] for p in parts if "inlineData" in p), None)

            if not image_data:
                return None

            ext = image_data.get("mimeType", "image/png").split("/")[-1]
            safe = "".join(c if c.isalnum() or c == "_" else "_" for c in title.lower())
            fname = f"{idx:02d}_{safe}.{ext}"
            fpath = media_dir / fname

            img_bytes = base64.b64decode(image_data["data"])
            fpath.write_bytes(img_bytes)

            return {
                "title": title,
                "path": str(fpath),
                "format": img.get("format", "landscape"),
                "size_kb": round(len(img_bytes) / 1024, 1),
                "source": "gemini",
                "mime_type": f"image/{ext}",
            }

        except Exception as e:
            self.logger.warning(f"Gemini image error: {e}")
            return None

    # ─── Prompt Enhancement ──────────────────────────────────────────────────

    def _enhance_prompt(self, img_prompt: dict) -> dict:
        """Wrap concept with style template based on format."""
        raw = img_prompt.get("prompt", "")
        fmt = img_prompt.get("format", "landscape").lower()
        cfg = FORMAT_CONFIG.get(fmt, FORMAT_CONFIG["landscape"])
        style = cfg["style"]

        # Strip redundant style words AI might have added
        clean = raw
        for rm in ["Cinematic,", "cinematic,", "8K,", "ultra-realistic,"]:
            clean = clean.replace(rm, "")
        clean = clean.strip(" ,.")

        enhanced = f"{clean}, {style}"

        return {**img_prompt, "enhanced_prompt": enhanced, "original_prompt": raw}

    def _default_prompts(self, topic: str) -> list:
        return [
            {
                "title": "Hero Visual (Facebook 16:9)", "format": "landscape",
                "prompt": (
                    f"Clean modern visualization representing {topic}, "
                    "elegant technology concept, soft lighting, "
                    "professional editorial style"
                ),
            },
            {
                "title": "Abstract Concept (Story 9:16)", "format": "portrait",
                "prompt": (
                    f"Premium abstract representation of {topic}, "
                    "soft gradients, clean aesthetic, space for text overlay"
                ),
            },
        ]

    # ─── Prompts Guide ───────────────────────────────────────────────────────

    def _save_prompts_guide(self, media_dir: Path, enhanced: list, topic: str):
        lines = [
            f"# 🎨 Image Prompts Guide — {topic}",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "วิธีใช้งาน:",
            "  A) ระบบจะสร้างรูปอัตโนมัติผ่าน Pollinations.ai (Flux) — ฟรี ไม่ต้อง key",
            "  B) Copy Enhanced Prompt ไปวางใน Google AI Studio / Midjourney / Ideogram",
            "=" * 60, "",
        ]
        for i, img in enumerate(enhanced, 1):
            fmt = img.get("format", "landscape")
            cfg = FORMAT_CONFIG.get(fmt, FORMAT_CONFIG["landscape"])
            lines += [
                f"## [{i}] {img.get('title', '')}",
                f"Format: {fmt.upper()} ({cfg['width']}x{cfg['height']}) | Style: {img.get('style', '')}",
                "",
                "### ✅ Enhanced Prompt (ready to use):",
                img.get("enhanced_prompt", img.get("prompt", "")),
                "",
                "### 📝 Original Concept (from AI):",
                img.get("original_prompt", img.get("prompt", "")),
                "", "-" * 40, "",
            ]
        (media_dir / "prompts_guide.txt").write_text("\n".join(lines), encoding="utf-8")

    def _create_ai_error(self, message: str):
        from common.error_handler import AIError
        return AIError(message, step_name="images", recoverable=True)

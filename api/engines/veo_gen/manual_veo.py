import os
import json
import base64
import logging
import requests
import sys
import mimetypes
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Try to import pyperclip for automatic copying
try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

# Setup paths relative to this script
SCRIPT_DIR = Path(__file__).parent.absolute()
ENV_PATH = SCRIPT_DIR / ".env"
CONFIG_PATH = SCRIPT_DIR / "config.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)

# --- Configuration Loader ---
def load_config():
    default_config = {
        "ai_settings": {
            "model_name": "google/gemini-2.0-flash-001",
            "system_prompt_file": "SystemPrompt_New.txt",
            "openclaw_url": "https://openrouter.ai/api/v1/chat/completions"
        },
        "video_settings": {
            "aspect_ratio": "9:16",
            "duration": "8s",
            "clips_count": 1,
            "style": "Commercial"
        },
        "paths": {
            "default_image": "input_product.jpg"
        }
    }
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_config
    return default_config

CONFIG = load_config()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENCLAW_API_URL = CONFIG["ai_settings"]["openclaw_url"]
MODEL_NAME = CONFIG["ai_settings"]["model_name"]
# Image path logic: check if absolute, otherwise relative to script or current dir
DEFAULT_IMAGE_NAME = CONFIG["paths"]["default_image"]

def encode_image(image_path: str) -> tuple[str, str]:
    """Encode image to base64 and return mime type, converting unsupported formats to JPEG."""
    try:
        from PIL import Image
        import io
        
        img = Image.open(image_path)
        # Convert everything to RGB (drops alpha/transparency, compatible with JPEG)
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8"), "image/jpeg"
    except ImportError:
        # Fallback if Pillow is not installed
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8"), mime_type

def generate_prompts(image_path: str) -> Optional[Dict[str, Any]]:
    """Analyze image and generate prompts using AI"""
    if not os.path.exists(image_path):
        print(f"❌ ไม่พบไฟล์รูปภาพ: {image_path}")
        return None

    print(f"🔍 กำลังวิเคราะห์รูปภาพ: {os.path.basename(image_path)}...")
    print(f"🤖 ใช้ AI Model: {MODEL_NAME}")
    print(f"⚙️ Config: {CONFIG['video_settings']['aspect_ratio']} | {CONFIG['video_settings']['duration']} | Style: {CONFIG['video_settings']['style']}")
    
    system_prompt_file = SCRIPT_DIR / CONFIG["ai_settings"]["system_prompt_file"]
    try:
        with open(system_prompt_file, "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        print(f"❌ ไม่พบไฟล์ {system_prompt_file}")
        return None

    try:
        base64_image, mime_type = encode_image(image_path)
    except Exception as e:
        print(f"❌ ไม่สามารถอ่านรูปภาพได้: {e}")
        return None

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5050",
        "X-Title": "OpenClaw VEO Tool"
    }

    # Inject config into user message to guide the AI
    user_instruction = (
        f"ช่วยวิเคราะห์รูปนี้และสร้าง JSON prompt สำหรับ Automation ด้วยเงื่อนไขดังนี้:\n"
        f"- สัดส่วนวิดีโอ: {CONFIG['video_settings']['aspect_ratio']}\n"
        f"- ความยาววิดีโอ: {CONFIG['video_settings']['duration']}\n"
        f"- สไตล์วิดีโอ: {CONFIG['video_settings']['style']}\n"
        f"กรุณาตอบมาแค่ JSON เท่านั้น"
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_instruction},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}},
                ],
            },
        ],
    }

    try:
        response = requests.post(OPENCLAW_API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            print(f"❌ API Error ({response.status_code}): {response.text}")
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip().strip("```json").strip("```").strip()
        return json.loads(content)
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเรียก API: {e}")
        return None

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="Path to product image")
    parser.add_argument("--json-output", action="store_true", help="Output only JSON")
    parser.add_argument("--aspect-ratio", help="Video aspect ratio")
    parser.add_argument("--duration", help="Video duration")
    parser.add_argument("--style", help="Video style")
    parser.add_argument("--clips-count", type=int, help="Number of clips")
    args = parser.parse_args()

    # Override config with args if provided
    if args.aspect_ratio:
        CONFIG["video_settings"]["aspect_ratio"] = args.aspect_ratio
    if args.duration:
        CONFIG["video_settings"]["duration"] = args.duration
    if args.style:
        CONFIG["video_settings"]["style"] = args.style
    if args.clips_count:
        CONFIG["video_settings"]["clips_count"] = args.clips_count

    # Image Selection Logic
    image_path = args.image
    if not image_path:
        # Check current dir first, then script dir
        if os.path.exists(DEFAULT_IMAGE_NAME):
            image_path = DEFAULT_IMAGE_NAME
        elif (SCRIPT_DIR / DEFAULT_IMAGE_NAME).exists():
            image_path = str(SCRIPT_DIR / DEFAULT_IMAGE_NAME)
        else:
            # Fallback to any image in script dir
            import glob
            images = glob.glob(str(SCRIPT_DIR / "*.jpg")) + glob.glob(str(SCRIPT_DIR / "*.png"))
            if images:
                image_path = images[0]
            else:
                if not args.json_output:
                    print("❌ ไม่พบรูปภาพสินค้า")
                sys.exit(1)

    data = generate_prompts(image_path)
    if not data:
        sys.exit(1)

    if args.json_output:
        print(json.dumps(data, ensure_ascii=False))
        return

    kf_prompt = data.get('keyframe_generation_prompt', '')
    veo_prompt = data.get('veo_video_prompt', '')

    print("\n" + "="*60)
    print("🚀 VEO Manual Prompt Tool (Engine Hub Integration)")
    print("="*60)
    print("\n✨ วิเคราะห์เสร็จแล้ว! ทำตามขั้นตอนดังนี้:\n")
    
    # STEP 1
    print("="*60)
    print("STEP 1: สร้างรูปภาพ Keyframe (ใช้ Nano Banana 2)")
    print("-" * 60)
    print(f"สัดส่วนที่ตั้งไว้: {CONFIG['video_settings']['aspect_ratio']}")
    print(f"1. เปิดเว็บ: https://labs.google/fx/th/tools/flow")
    print(f"2. อัปโหลดรูป: {os.path.basename(image_path)}")
    print("3. คัดลอก Prompt ด้านล่างไปวางในช่องแชท:")
    print("\n--- [ PROMPT STEP 1 ] ---")
    print(kf_prompt)
    print("------------------------")
    
    if HAS_PYPERCLIP:
        try:
            pyperclip.copy(kf_prompt)
            print("\n✅ (คัดลอกลง Clipboard ให้แล้ว!)")
        except:
            pass

    # STEP 2
    print("\n" + "="*60)
    print("STEP 2: สร้างวิดีโอ (ใช้ Veo 3.1)")
    print("-" * 60)
    print(f"ความยาวที่ตั้งไว้: {CONFIG['video_settings']['duration']}")
    print("1. กดปุ่ม 'เริ่ม' (Start) ที่รูปเดิม")
    print("2. คัดลอก Prompt ด้านล่างไปวาง:")
    print("\n--- [ PROMPT STEP 2 ] ---")
    print(veo_prompt)
    print("------------------------")
    
    print("\n3. เลือกโมเดล 'Veo 3.1' และกด Enter")
    print("="*60)

    print("\n📜 ข้อมูลเพิ่มเติม:")
    print(f"🤖 AI Model (Prompt Gen): {MODEL_NAME}")
    print(f"📦 สินค้า: {data.get('product_analysis', 'N/A')}")
    print(f"🧬 สไตล์ตัวละคร: {data.get('character_dna', 'N/A')[:100]}...")
    print("\n🎬 เสร็จเรียบร้อย! ขอให้ได้วิดีโอสวยๆ นะครับ")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

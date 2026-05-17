#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContentWriter - Tech Analyst Edition for "lookforward"
Focused on: Authority, Depth, and Future Vision.
Supports Multi-Modal Generation (Text + Visual Prompts).
"""

import sys
import os
import json
import requests
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import (
    setup_logger, get_date_str, ensure_dir, sanitize_filename,
    print_header, print_success, print_error, print_info
)
from shared.config import get_config
from shared.ai_client import create_ai_client


class ContentWriter:
    """
    Generate high-authority tech analysis posts for the lookforward page.
    Supports multi-modal generation (Text + Visual Prompts).
    """
    
    def __init__(self):
        """Initialize writer with lookforward configuration."""
        self.config = get_config()
        self.logger = setup_logger(
            "ContentWriter",
            self.config.paths["error_logs"] / f"{get_date_str()}_ContentWriter.log"
        )
        self.ai = create_ai_client(self.logger)
        
        # System prompt for multi-modal generation
        self.system_prompt = """You are the Lead Tech Analyst & Visual Strategist for "lookforward".

## Mission
Create authority content AND visual prompts that share the SAME VISION.
Everything must meet "lookforward Authority Standards".

## Authority Standards
1. **Facts First**: Verifiable claims only.
2. **Systemic Analysis**: Explain mechanisms/structures, not just news.
3. **No Hype**: No "revolutionary", "game-changing" without proof.
4. **No AI-Speak**: Natural, professional Thai (Calm & Sharp).
5. **User-Centric**: actionable insights.

## Content Structure (Facebook)
- Length: 800-1200 characters (NOT words).
- Elements: Hook, Facts, Tech Breakdown, Impact, Vision, CTA.
- Tone: Insightful, Professional, Visionary.

## Visual Strategy
- Create 2 prompts for gemini-2.5-flash-image (Nano Banana).
- Aspect Ratio: 9:16 (Vertical) for mobile.
- Style: Editorial tech, minimal, modern, abstract data visualization.
- Text Overlay: Max 5 words.

## Output Format (JSON Only)
{
  "content": {
    "platform": "Facebook",
    "text": "...",
    "char_count": 0,
    "insight_score": 5,
    "style": "..."
  },
  "image_prompts": [
    {"title": "...", "prompt": "...", "aspect_ratio": "9:16"},
    {"title": "...", "prompt": "...", "aspect_ratio": "9:16"}
  ],
  "caption": "...",
  "hashtags": ["#tag1", "#tag2"]
}
"""

    def generate_post(
        self,
        topic: str,
        platform: str = "facebook",
        hook: str = None,
        cta: str = None,
        tone: str = "professional"
    ) -> str:
        """
        Legacy method kept for backward compatibility.
        Redirects to generate_content_with_visuals but returns only text.
        """
        result = self.generate_content_with_visuals(topic, context=f"Tone: {tone}", style=tone)
        return result.get("content", {}).get("text", "")

    def generate_content_with_visuals(self, topic: str, context: str, style: str = "Contrarian") -> dict:
        """
        Generate content + visual prompts in one go using Gemini 2.5 Flash.
        Returns a dictionary with content and image prompts.
        """
        print_header(f"🎨 Generative Studio: {topic}")
        print_info(f"Style: {style}")

        user_prompt = f"""Topic: {topic}

Context/Strategy:
{context}

Style: {style}

Output: Valid JSON only.
"""
        
        # We need to bypass the standard client for JSON mode enforcement on Gemini
        gemini_key = self.config.get_api_key("gemini") or os.getenv("GOOGLE_API_KEY")
        
        if not gemini_key:
            self.logger.error("No Google API Key found via text config or env.")
            return {}

        model = "models/gemini-2.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={gemini_key}"
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": self.system_prompt}]},
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8000,
                "responseMimeType": "application/json"
            }
        }
        
        print_info("⏳ Calling Gemini 2.5 Flash (Multi-Modal)...")
        
        try:
            response = requests.post(url, json=payload, timeout=90)
            
            if response.status_code != 200:
                error_msg = f"API Error {response.status_code}: {response.text[:200]}"
                self.logger.error(error_msg)
                print_error(error_msg)
                return {}
            
            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                print_error("No candidates in response")
                return {}
                
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(content_text)
            
            # Validation / Fixes
            if "content" in data and "text" in data["content"]:
                char_count = len(data["content"]["text"])
                data["content"]["char_count"] = char_count
                print_success(f"Generated Content: {char_count} chars (Insight: {data['content'].get('insight_score', '?')}/5)")
            
            if "image_prompts" in data:
                print_success(f"Generated {len(data['image_prompts'])} Visual Prompts")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            print_error(f"Generation failed: {e}")
            return {}

    def save_output(self, topic: str, data: dict) -> Path:
        """Save the generated multi-modal content to Drafts."""
        if not data:
            return None
            
        date_str = get_date_str()
        draft_dir = self.config.paths["drafts"] / date_str
        ensure_dir(draft_dir)
        
        safe_topic = sanitize_filename(topic)[:50]
        timestamp = datetime.now().strftime("%H%M%S")
        base_name = f"{safe_topic}_{timestamp}"
        
        # Save JSON Data
        json_file = draft_dir / f"{base_name}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        # Save Markdown Content for Review
        md_file = draft_dir / f"{base_name}.md"
        content = data.get("content", {})
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# {topic}\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Insight Score**: {content.get('insight_score', 'N/A')}/5\n")
            f.write(f"**Chars**: {content.get('char_count', 0)}\n")
            f.write(f"**Style**: {data.get('content', {}).get('style', 'N/A')}\n\n")
            f.write("---\n\n")
            f.write(content.get("text", ""))
            f.write("\n\n---\n\n")
            f.write(f"**Caption**: {data.get('caption', '')}\n\n")
            f.write(f"**Hashtags**: {' '.join(data.get('hashtags', []))}\n\n")
            f.write("---\n\n")
            f.write("## 🖼️ Visual Prompts\n")
            for i, img in enumerate(data.get("image_prompts", []), 1):
                f.write(f"### Image {i}: {img.get('title', 'Untitled')}\n")
                f.write(f"**Prompt**: {img.get('prompt', '')}\n\n")
        
        print_success(f"Draft saved: {md_file}")
        return md_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ContentWriter Standalone Test")
    parser.add_argument("--topic", help="Topic to write about")
    parser.add_argument("--context", help="Context or strategy for the topic")
    
    args = parser.parse_args()
    
    writer = ContentWriter()
    
    if args.topic and args.context:
        print_info(f"Running manual writer for: {args.topic}")
        data = writer.generate_content_with_visuals(args.topic, args.context)
        writer.save_output(args.topic, data)
    else:
        # Default test case
        topic = "Kimi K2.5 - AI Model ที่ถูกกว่า GPT-4o 90%"
        context = "DeepSeek เปิดตัว Kimi K2.5 ราคา $1.50/1M tokens, เร็วกว่า R1 3-5 เท่า, MoE architecture."
        print_info("Running default test case...")
        data = writer.generate_content_with_visuals(topic, context)
        writer.save_output(topic, data)

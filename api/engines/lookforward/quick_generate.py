#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Content Generator for lookforward
Generate content for OpenAI DeepSeek topic
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_KEY_HERE")
TOPIC = os.getenv("CURRENT_TOPIC", "OpenAI DeepSeek - เจาะลึก AI Model ที่โลกจับตา")

def generate_content():
    """Generate lookforward content using Gemini"""
    
    system_prompt = """You are the Lead Tech Strategist for lookforward.
Analyze the topic and create high-authority content (Insight Score 5/5).

## Core Task
Dissect the topic to find the "Real Value" vs "Hype".

## Output Format (JSON):
{
  "strategy": "Detailed analysis of the topic",
  "content": {
    "text": "Main content (300-400 words, Thai language, sharp and insightful tone)",
    "insight_score": 5,
    "char_count": 350
  },
  "caption": "Hook sentence (1 line)",
  "hashtags": ["#lookforward", "#AI", "#DeepSeek"]
}
"""

    user_prompt = f"""Analyze this topic for a tech authority post: {TOPIC}

Requirements:
- Write in Thai language
- Sharp, insightful tone (not casual)
- Focus on non-obvious angles
- 300-400 words
- Include caption and hashtags"""

    model = "models/gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8000
        }
    }
    
    try:
        print("🧠 Generating content with Gemini 2.5 Flash...")
        response = requests.post(url, json=payload, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]
            print("✅ Content generated successfully!")
            return content_text
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def save_content(content_text):
    """Save content to drafts folder"""
    
    # Create folder structure
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M%S")
    
    # OpenClaw integrated path
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    draft_dir = root_dir / "data" / "content" / "lookforward" / date_str / f"OpenAI_DeepSeek_{timestamp}"
    draft_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving to: {draft_dir}")
    
    # Save raw content
    with open(draft_dir / "02_content.md", 'w', encoding='utf-8') as f:
        f.write(f"# {TOPIC}\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        f.write(content_text)
        f.write("\n\n---\n")
    
    print(f"✅ Content saved!")
    print(f"📁 Location: {draft_dir}")
    
    return draft_dir


def main():
    print("🦞 lookforward Content Generator")
    print(f"📝 Topic: {TOPIC}\n")
    
    # Generate content
    content = generate_content()
    
    if not content:
        print("\n❌ Failed to generate content")
        return
    
    # Save content
    folder = save_content(content)
    
    print(f"\n✅ Done! Content ready for 22:00 post")
    print(f"📍 Check: {folder}")


if __name__ == "__main__":
    main()

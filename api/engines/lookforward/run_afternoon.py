#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lookforward Afternoon Post Generator
Standalone script for generating afternoon content (13:00)
Uses Groq API (free, fast) for reliable generation
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime

# Fix encoding for Thai characters
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load .env file
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()

# API Configuration
GROQ_KEY = os.getenv("GROQ_API_KEY")
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_KEY_B2 = os.getenv("GOOGLE_API_KEY_BACKUP2")

if not GROQ_KEY:
    print("ERROR: GROQ_API_KEY not found in .env")
    sys.exit(1)

print("Using Groq API (llama-3.3-70b) for content generation")

# Topic for afternoon post - using AI Agent memory as trending topic
TOPIC = os.getenv("CURRENT_TOPIC", "AI Agent Memory Systems - เทคโนโลยีที่ทำให้ AI จดจำได้แม่นยำขึ้น")


def generate_content_groq(topic):
    """Generate content using Groq API with Llama"""
    
    system_prompt = """You are the Lead Tech Strategist for lookforward page.
Write tech authority content in Thai with Insight Score 5/5.

## Output JSON ONLY:
{
  "content": {
    "text": "Full article in Thai (300-400 words, sharp and insightful)",
    "insight_score": 5,
    "char_count": 0
  },
  "caption": "Hook sentence for Facebook post (1-2 lines)",
  "hashtags": ["#lookforward", "#AI", "#Tech"]
}
"""
    
    user_prompt = f"""Analyze this topic for a tech authority post in Thai: {topic}

Requirements:
- Write in Thai language
- Sharp, insightful tone (not casual)
- Focus on non-obvious angles
- 300-400 words
- Include caption and hashtags
- Return valid JSON only"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }
    
    try:
        print(f"Generating content for: {topic}")
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            content_text = result["choices"][0]["message"]["content"]
            print("SUCCESS: Content generated!")
            return content_text
        else:
            print(f"ERROR: API returned {response.status_code}")
            print(response.text[:500])
            return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def generate_content_gemini(topic, api_key):
    """Generate content using Gemini API"""
    
    system_prompt = """You are the Lead Tech Strategist for lookforward page.
Write tech authority content in Thai with Insight Score 5/5.

## Output JSON ONLY:
{
  "content": {
    "text": "Full article in Thai (300-400 words, sharp and insightful)",
    "insight_score": 5,
    "char_count": 0
  },
  "caption": "Hook sentence for Facebook post (1-2 lines)",
  "hashtags": ["#lookforward", "#AI", "#Tech"]
}
"""
    
    user_prompt = f"""Analyze this topic for a tech authority post in Thai: {topic}

Requirements:
- Write in Thai language
- Sharp, insightful tone (not casual)
- Focus on non-obvious angles
- 300-400 words
- Include caption and hashtags"""

    model = "models/gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8000
        }
    }
    
    try:
        print(f"Generating content for: {topic}")
        response = requests.post(url, json=payload, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            content_text = result["candidates"][0]["content"]["parts"][0]["text"]
            print("SUCCESS: Content generated!")
            return content_text
        else:
            print(f"ERROR: API returned {response.status_code}")
            return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def save_content(content_text, topic, source="groq"):
    """Save content to drafts folder"""
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M%S")
    
    # Use OpenClaw dashboard data folder
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    data_dir = root_dir / "data" / "content" / "lookforward"
    
    # Create folder
    safe_topic = "".join(c if c.isalnum() else "_" for c in topic[:30])
    draft_dir = data_dir / date_str / f"{safe_topic}_{timestamp}"
    draft_dir.mkdir(parents=True, exist_ok=True)
    
    # Save content
    post_file = draft_dir / "post.txt"
    caption_file = draft_dir / "caption.txt"
    hashtags_file = draft_dir / "hashtags.txt"
    metadata_file = draft_dir / "metadata.json"
    
    try:
        # Parse JSON content
        json_str = content_text.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif json_str.startswith("```"):
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        data = json.loads(json_str)
        
        # Save post content
        with open(post_file, 'w', encoding='utf-8') as f:
            f.write(data.get("content", {}).get("text", ""))
        
        # Save caption
        with open(caption_file, 'w', encoding='utf-8') as f:
            f.write(data.get("caption", ""))
        
        # Save hashtags
        with open(hashtags_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(data.get("hashtags", [])))
        
        # Save metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                "topic": topic,
                "generated": datetime.now().isoformat(),
                "insight_score": data.get("content", {}).get("insight_score", 5),
                "char_count": len(data.get("content", {}).get("text", "")),
                "source": source
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\nSAVED to: {draft_dir}")
        return draft_dir
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        # Save raw content as fallback
        with open(draft_dir / "raw_content.txt", 'w', encoding='utf-8') as f:
            f.write(content_text)
        print(f"Raw content saved to: {draft_dir / 'raw_content.txt'}")
        return draft_dir


def main():
    print("=" * 60)
    print("Lookforward Afternoon Post Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Topic: {TOPIC}")
    print("=" * 60)
    
    # Generate content - try Groq first, then Gemini backup
    content = generate_content_groq(TOPIC)
    
    if not content and GEMINI_KEY:
        print("\nGroq failed, trying Gemini...")
        content = generate_content_gemini(TOPIC, GEMINI_KEY)
    
    if not content and GEMINI_KEY_B2:
        print("\nPrimary Gemini failed, trying backup...")
        content = generate_content_gemini(TOPIC, GEMINI_KEY_B2)
    
    if not content:
        print("\nFAILED to generate content - all APIs failed")
        sys.exit(1)
    
    # Save content
    folder = save_content(content, TOPIC)
    
    print("\n" + "=" * 60)
    print("COMPLETE! Afternoon post ready.")
    print(f"Location: {folder}")
    print("=" * 60)


if __name__ == "__main__":
    main()
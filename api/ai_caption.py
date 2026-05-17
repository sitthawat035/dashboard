# ╔═══════════════════════════════════════════════════════╗
# ║  api/ai_caption.py — AI Caption Generator            ║
# ╚═══════════════════════════════════════════════════════╝

"""
GET /api/ai_caption/generate?text=<seed_text>
POST /api/ai_caption/generate
  Body: { "text": "...", "style": "engaging|humor|professional", "platform": "twitter|instagram|facebook" }

Generates engaging captions using a simple heuristic + Markov-chain
inspired approach. For production, swap in an LLM API call.
"""

import os
import re
import random
import json
from flask import Blueprint, request, jsonify

from api.auth import login_required

ai_caption_bp = Blueprint("ai_caption", __name__)

# ─── Caption Templates ─────────────────────────────────────────────────────────

ADJECTIVES = [
    "mind-blowing", "incredible", "unbelievable", "jaw-dropping", "epic",
    "insane", "legendary", "absolute", "pure", "next-level",
]

HOOKS = [
    "You won't believe...", "Here's why...", "This changes everything.",
    "Stop what you're doing...", "Read this before...", "The truth about...",
    "Why everyone is talking about...", "This is wild...", "Facts you need to know...",
    "Breaking:", "Exclusive:", "Breaking news:",
]

CALLS_TO_ACTION = [
    "Drop a 🔥 if you agree!",
    "Comment below! 👇",
    "Share with someone who needs this!",
    "Tag someone who needs to see this!",
    "Save this for later! 📌",
    "Follow for more! 🚀",
    "Turn on post notifications! 🔔",
    "Link in bio for more!",
    "Double tap if you loved this! ❤️",
    "Repost to your story! ✨",
]

EMOJI_CLUSTERS = [
    "🔥💯🙌", "🚀✨👀", "💡👇❤️", "😱🤯💥", "🙌🔝✨",
    "💯🔥👇", "🤩😭🙌", "👀💥🚀", "❤️‍🔥📌✨", "😎🔥💯",
]

# ─── Markov Chain Caption Generator ──────────────────────────────────────────

class CaptionGenerator:
    """Simple word-chain generator for captions."""

    def __init__(self):
        self.chains = {}
        self.corpus = [
            # Thai-tech engaging phrases
            "AI is reshaping the way we create content forever",
            "The future of social media is here and it's powered by AI",
            "This algorithm update will change your feed forever",
            "SpaceX just accomplished something incredible",
            "The next generation of tech is closer than you think",
            "Scientists discover breakthrough in renewable energy",
            "This robot just passed a major milestone",
            "The internet is going crazy over this new discovery",
            "China's latest tech advancement shocks the world",
            "Everything is about to change in the AI industry",
            # General engaging content
            "This is the most important thing you'll read today",
            "The data doesn't lie — here are the facts",
            "Why this is trending everywhere right now",
            "The real story behind this viral moment",
            "Here's what nobody is telling you about this",
        ]

    def _build_chain(self, words):
        for i in range(len(words) - 1):
            key = words[i].lower()
            next_word = words[i + 1].lower()
            if key not in self.chains:
                self.chains[key] = []
            self.chains[key].append(next_word)

    def generate(self, seed_word=None, max_words=30):
        for line in self.corpus:
            words = re.findall(r"\w+", line)
            if len(words) >= 2:
                self._build_chain(words)

        if not self.chains:
            return "Something amazing is happening! Check it out!"

        if seed_word and seed_word.lower() in self.chains:
            current = seed_word.lower()
        else:
            keys = list(self.chains.keys())
            current = random.choice(keys)

        words = [current.capitalize()]
        visited = set()

        for _ in range(max_words - 1):
            if current not in self.chains:
                break
            choices = self.chains[current]
            next_word = random.choice(choices)

            # Avoid repetition
            if len(words) > 3 and next_word in words[-3:]:
                candidates = [c for c in choices if c != next_word]
                if candidates:
                    next_word = random.choice(candidates)

            words.append(next_word.capitalize())
            key = next_word
            if key in visited and len(visited) < len(self.chains) // 2:
                break
            visited.add(key)
            current = key

        caption = " ".join(words)
        # Add punctuation
        if not caption.endswith((".", "!", "?", "🔥", "💯")):
            caption += "."
        return caption

# Singleton generator
_generator = CaptionGenerator()

# ─── Routes ───────────────────────────────────────────────────────────────────

@ai_caption_bp.route("/api/ai_caption/generate", methods=["GET", "POST"])
@login_required
def generate_caption():
    """
    Generate an AI-powered caption.
    GET: /api/ai_caption/generate?text=seed_word&style=engaging&platform=twitter
    POST: { "text": "...", "style": "...", "platform": "..." }
    """
    if request.method == "GET":
        seed = request.args.get("text", "")
        style = request.args.get("style", "engaging")
        platform = request.args.get("platform", "general")
    else:
        data = request.json or {}
        seed = data.get("text", "")
        style = data.get("style", "engaging")
        platform = data.get("platform", "general")

    # Generate base caption
    base_caption = _generator.generate(seed_word=seed if seed else None)

    # Style variations
    if style == "humor":
        base_caption = base_caption.replace(".", " 😂").replace("!", " 🤣")

    # Platform-specific tweaks
    char_limits = {"twitter": 280, "instagram": 2200, "facebook": 63206, "youtube": 5000}
    limit = char_limits.get(platform, 280)

    if len(base_caption) > limit:
        base_caption = base_caption[: limit - 3] + "..."

    # Add variety elements
    options = {
        "caption": base_caption,
        "hashtags": _generate_hashtags(seed),
        "emoji_cluster": random.choice(EMOJI_CLUSTERS),
        "call_to_action": random.choice(CALLS_TO_ACTION) if random.random() > 0.5 else "",
    }

    return jsonify({
        "success": True,
        "caption": options["caption"],
        "hashtags": options["hashtags"],
        "emoji_cluster": options["emoji_cluster"],
        "call_to_action": options["call_to_action"],
        "full_post": f"{options['caption']}\n\n{options['emoji_cluster']}\n\n{options['hashtags']}\n{options['call_to_action']}",
    })

@ai_caption_bp.route("/api/ai_caption/styles", methods=["GET"])
def get_styles():
    """List available caption styles."""
    return jsonify({
        "styles": [
            {"id": "engaging", "label": "Engaging", "description": "Hook + value + CTA"},
            {"id": "humor", "label": "Humor", "description": "Funny and relatable"},
            {"id": "professional", "label": "Professional", "description": "Clean and informative"},
            {"id": "viral", "label": "Viral", "description": "Clickbait-style hooks"},
        ],
        "platforms": ["twitter", "instagram", "facebook", "youtube"],
    })

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_hashtags(seed="", count=5):
    """Generate relevant hashtags based on seed text."""
    base_tags = ["#trending", "#viral", "#fyp", "#tech", "#news", "#ai", "#innovation"]
    tech_tags = ["#technology", "#AI", "#machinelearning", "#futuretech", "#innovation"]
    space_tags = ["#spacex", "#space", "#nasa", "#elonmusk", "#starship"]

    if seed:
        seed_lower = seed.lower()
        if any(w in seed_lower for w in ["space", "rocket", "falcon", "starship"]):
            tags = space_tags
        elif any(w in seed_lower for w in ["ai", "robot", "tech", "data"]):
            tags = tech_tags
        else:
            tags = base_tags
    else:
        tags = base_tags

    selected = random.sample(tags, min(count, len(tags)))
    return " ".join(selected)

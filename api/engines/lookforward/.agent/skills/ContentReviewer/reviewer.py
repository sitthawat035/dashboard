#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContentReviewer - Quality control for posts (100% FREE, rule-based)

Usage:
    python reviewer.py --draft 04_Drafts/2026-02-07/facebook_viral_trend.md
    python reviewer.py --text "Your post text here" --platform facebook
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import (
    setup_logger, load_markdown, save_markdown,
    get_date_str, ensure_dir,
    print_header, print_success, print_error, print_info
)
from shared.config import get_config


class ContentReviewer:
    """
    Review and score content quality (100% FREE, rule-based).
    """
    
    def __init__(self):
        """Initialize reviewer."""
        self.config = get_config()
        self.logger = setup_logger(
            "ContentReviewer",
            self.config.paths["error_logs"] / f"{get_date_str()}_ContentReviewer.log"
        )
        # Handle brand_guidelines as string or dict
        brand = self.config.brand_guidelines
        if isinstance(brand, dict):
            self.brand = brand
        else:
            # Default brand settings if not a dict
            self.brand = {"tone": "casual", "voice": "friendly"}
    
    def score_post(self, text: str, platform: str) -> dict:
        """
        Score post quality (0-100).
        
        Args:
            text: Post text
            platform: Platform name
            
        Returns:
            Score dictionary with breakdown
        """
        score = 0
        feedback = []
        
        # Get platform config
        platforms = self.config.get_platform_config()
        p_config = platforms.get(platform.lower(), platforms["facebook"])
        
        # 1. Length Check (20 points)
        length = len(text)
        optimal = p_config["optimal_length"]
        max_len = p_config["max_length"]
        
        if length > max_len:
            feedback.append(f"❌ ยาวเกินไป: {length}/{max_len} ตัวอักษร")
        elif optimal[0] <= length <= optimal[1]:
            score += 20
            feedback.append(f"✅ ความยาวเหมาะสม: {length} ตัวอักษร")
        elif length < optimal[0]:
            score += 10
            feedback.append(f"⚠️  สั้นไป: {length}/{optimal[0]} ตัวอักษร")
        else:
            score += 15
            feedback.append(f"⚠️  ยาวไป: {length}/{optimal[1]} ตัวอักษร")
        
        # 2. Hashtag Count (15 points)
        hashtags = re.findall(r'#\w+', text)
        h_min, h_max = p_config["hashtag_count"]
        
        if h_min <= len(hashtags) <= h_max:
            score += 15
            feedback.append(f"✅ แฮชแท็กเหมาะสม: {len(hashtags)} อัน")
        elif len(hashtags) < h_min:
            score += 7
            feedback.append(f"⚠️  แฮชแท็กน้อยไป: {len(hashtags)}/{h_min}")
        else:
            score += 7
            feedback.append(f"⚠️  แฮชแท็กเยอะไป: {len(hashtags)}/{h_max}")
        
        # 3. Emoji Usage (15 points)
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        emojis = emoji_pattern.findall(text)
        
        if 2 <= len(emojis) <= 5:
            score += 15
            feedback.append(f"✅ อิโมจิเหมาะสม: {len(emojis)} อัน")
        elif len(emojis) == 0:
            score += 5
            feedback.append("⚠️  ไม่มีอิโมจิ (ควรมี 2-5 อัน)")
        elif len(emojis) < 2:
            score += 10
            feedback.append(f"⚠️  อิโมจิน้อยไป: {len(emojis)} อัน")
        else:
            score += 8
            feedback.append(f"⚠️  อิโมจิเยอะไป: {len(emojis)} อัน")
        
        # 4. CTA Present (20 points)
        cta_keywords = ["แชร์", "แท็ก", "กดไลค์", "คอมเมนต์", "บอกต่อ", "ลิงก์", "ดูเพิ่ม"]
        has_cta = any(keyword in text for keyword in cta_keywords)
        
        if has_cta:
            score += 20
            feedback.append("✅ มี Call to Action")
        else:
            feedback.append("❌ ไม่มี Call to Action")
        
        # 5. Hook/Attention Grabber (15 points)
        hook_patterns = [
            r'^[🔥✨💡📌💥]',  # Starts with attention emoji
            r'[!?]{1,2}',     # Has exclamation/question
            r'รู้ยัง|ทำไม|อย่าพลาด|ว้าว',  # Thai hooks
        ]
        
        has_hook = any(re.search(pattern, text) for pattern in hook_patterns)
        
        if has_hook:
            score += 15
            feedback.append("✅ มี Hook ดึงดูดความสนใจ")
        else:
            score += 7
            feedback.append("⚠️  ควรเพิ่ม Hook ดึงดูดความสนใจ")
        
        # 6. Tone Check (15 points)
        tone = self.brand.get("tone", "casual")
        
        # Simple tone detection
        friendly_markers = ["ครับ", "ค่ะ", "เพื่อน", "พี่น้อง", "555"]
        formal_markers = ["บริษัท", "ผู้บริโภค", "กรุณา"]
        
        friendly_count = sum(1 for m in friendly_markers if m in text)
        formal_count = sum(1 for m in formal_markers if m in text)
        
        if tone == "casual" and friendly_count > formal_count:
            score += 15
            feedback.append("✅ โทนเป็นกันเอง ตรงแบรนด์")
        elif tone == "professional" and formal_count > friendly_count:
            score += 15
            feedback.append("✅ โทนเป็นทางการ ตรงแบรนด์")
        else:
            score += 10
            feedback.append(f"⚠️  โทนไม่ค่อยชัดเจน (ต้องการ: {tone})")
        
        return {
            "score": score,
            "grade": self._get_grade(score),
            "feedback": feedback,
            "metrics": {
                "length": length,
                "hashtags": len(hashtags),
                "emojis": len(emojis),
                "has_cta": has_cta,
                "has_hook": has_hook
            }
        }
    
    def _get_grade(self, score: int) -> str:
        """Get letter grade from score."""
        if score >= 90:
            return "A (ดีเยี่ยม - พร้อมโพสต์เลย!)"
        elif score >= 80:
            return "B (ดี - ปรับแต่งนิดหน่อย)"
        elif score >= 70:
            return "C (พอใช้ - ควรปรับปรุง)"
        elif score >= 60:
            return "D (ต่ำ - ต้องแก้ไข)"
        else:
            return "F (ไม่ผ่าน - เขียนใหม่)"
    
    def review_and_save(self, text: str, platform: str, output_path: Path = None) -> dict:
        """
        Review post and save report.
        
        Args:
            text: Post text
            platform: Platform name
            output_path: Optional output path
            
        Returns:
            Review results
        """
        print_header(f"📋 CONTENT REVIEW - {platform.upper()}")
        
        # Score post
        result = self.score_post(text, platform)
        
        # Display results
        print_info(f"\n📊 SCORE: {result['score']}/100")
        print_info(f"📝 GRADE: {result['grade']}\n")
        
        print_info("FEEDBACK:")
        for item in result['feedback']:
            print_info(f"  {item}")
        
        # Save report if requested
        if output_path:
            report = self._generate_report(text, platform, result)
            save_markdown(report, output_path)
            print_success(f"\n✅ Report saved: {output_path}")
        
        return result
    
    def _generate_report(self, text: str, platform: str, result: dict) -> str:
        """Generate markdown review report."""
        lines = [
            f"# Content Review Report\n",
            f"**Platform**: {platform}  ",
            f"**Reviewed**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            "---\n",
            f"## 📊 Score: {result['score']}/100\n",
            f"**Grade**: {result['grade']}\n",
            "## 📝 Feedback\n"
        ]
        
        for item in result['feedback']:
            lines.append(f"- {item}")
        
        lines.extend([
            "\n## 📈 Metrics\n",
            f"- **Length**: {result['metrics']['length']} characters",
            f"- **Hashtags**: {result['metrics']['hashtags']}",
            f"- **Emojis**: {result['metrics']['emojis']}",
            f"- **Has CTA**: {'✅ Yes' if result['metrics']['has_cta'] else '❌ No'}",
            f"- **Has Hook**: {'✅ Yes' if result['metrics']['has_hook'] else '❌ No'}\n",
            "## ✍️ Original Post\n",
            "```",
            text,
            "```\n"
        ])
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Review content quality (FREE)")
    parser.add_argument(
        "--draft",
        help="Path to draft markdown file"
    )
    parser.add_argument(
        "--text",
        help="Post text to review"
    )
    parser.add_argument(
        "--platform",
        default="facebook",
        help="Platform (facebook, tiktok, instagram, twitter)"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save review report"
    )
    
    args = parser.parse_args()
    
    # Get text to review
    if args.draft:
        content = load_markdown(args.draft)
        # Extract first post variation (simplified)
        # In production, parse properly
        text = content.split("```")[1] if "```" in content else content[:500]
        platform = args.platform
    elif args.text:
        text = args.text
        platform = args.platform
    else:
        print_error("Must specify either --draft or --text")
        return
    
    # Create reviewer
    reviewer = ContentReviewer()
    
    # Review
    output_path = None
    if args.save_report:
        config = get_config()
        output_dir = config.paths["drafts"] / "reviews" / get_date_str()
        ensure_dir(output_dir)
        output_path = output_dir / f"review_{datetime.now().strftime('%H%M%S')}.md"
    
    result = reviewer.review_and_save(text, platform, output_path)
    
    # Decision
    if result["score"] >= 80:
        print_success("\n✅ APPROVED - Ready to post!")
    elif result["score"] >= 70:
        print_info("\n⚠️  NEEDS MINOR EDITS - Review feedback")
    else:
        print_error("\n❌ NEEDS MAJOR REVISION - See feedback above")


if __name__ == "__main__":
    main()

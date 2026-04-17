#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaSourcing - Tech Visual Scout for "lookforward"
Prioritizes technical evidence over generic stock.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import (
    setup_logger, get_date_str, ensure_dir,
    print_header, print_success, print_error, print_info
)
from shared.config import get_config
from shared.ai_client import create_ai_client

class MediaDownloader:
    """
    Finds and 'downloads' (simulates) technical visuals for lookforward.
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger(
            "MediaSourcing",
            self.config.paths["error_logs"] / f"{get_date_str()}_MediaSourcing.log"
        )
        self.ai = create_ai_client(self.logger)

    def suggest_visuals(self, content_draft: str) -> str:
        """
        Analyze content to suggest the most credible visual evidence.
        """
        system_prompt = f"""คุณคือ 'Technical Creative Director' ประจำเพจ lookforward
หน้าที่คือการออกแบบภาพประกอบที่ 'พิสูจน์' และ 'อธิบาย' ข้อมูลเทคโนโลยีที่ซับซ้อนให้เข้าใจง่ายและน่าเชื่อถือ

🚨 กฎการเลือกภาพ (Visual Integrity):
1. **Evidence-Based**: เน้นภาพ Screenshot, Chart, หรือ Diagram ที่อ้างอิงจากข้อมูลจริง
2. **Anti-Stock**: ห้ามแนะนำภาพ Stock Photo ที่มีคนยิ้มปลอม ๆ
3. **Professional Look**: เน้นโทนสีที่ดู Modern, Clean และ Minimalist
"""

        user_prompt = f"""วิเคราะห์เนื้อหานี้และแนะนำ 'ภาพประกอบที่ควรใช้' เพื่อเพิ่มความน่าเชื่อถือ:
---
{content_draft}
---
แนะนำภาพมา 1-2 ไอเดีย (เช่น Screenshot ของหน้านี้, กราฟเปรียบเทียบสิ่งนี้)"""

        if self.ai:
            try:
                print_info("📸 Designing technical visuals for the post...")
                suggestions = self.ai.generate(user_prompt, system=system_prompt)
                return suggestions.strip()
            except Exception as e:
                print_error(f"❌ Visual design failed: {e}")
        
        return "⚠️ แนะนำให้ใช้ Screenshot จริงจากหน้าเว็บของเทคโนโลยีนี้"

    def process_media(self, topic: str, content: str):
        """Simulate the media sourcing process."""
        output_dir = self.config.paths["media"] / get_date_str()
        ensure_dir(output_dir)
        
        suggestions = self.suggest_visuals(content)
        
        # In a real setup, this would trigger a search/download script
        print_success(f"✅ Visual Strategy for '{topic}':")
        print(f"\n{suggestions}\n")
        
        return suggestions

def main():
    print_header("📸 LOOKFORWARD VISUAL SCOUT")
    downloader = MediaDownloader()
    # Logic to read from draft would go here
    print_info("Ready to source technical evidence.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendResearcher - Tech Scout Edition for "lookforward"
Scans for high-signal technical innovation.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils import (
    setup_logger, load_markdown, save_markdown,
    get_date_str, ensure_dir, sanitize_filename,
    print_header, print_success, print_error, print_info
)
from shared.config import get_config
from shared.ai_client import create_ai_client

class TrendResearcher:
    """
    Scouts for high-authority tech and AI trends.
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger(
            "TrendResearcher",
            self.config.paths["error_logs"] / f"{get_date_str()}_TrendResearcher.log"
        )
        self.ai = create_ai_client(self.logger)

    def scan_sources(self) -> str:
        """
        Simulate scanning process for high-signal sources.
        """
        system_prompt = f"""คุณคือ 'Tech Intelligence Officer' ประจำเพจ lookforward
หน้าที่คือการเฟ้นหาข่าวสารที่ล้ำหน้าและมีคุณค่าเชิงวิชาการ/เทคนิค (AI, Tech, Crypto)

🚨 กฎการค้นหา (High-Signal Policy):
1. **Source Reliability**: เน้นข้อมูลจาก ArXiv, GitHub, Whitepapers, และ Official Blogs
2. **Technical Depth**: เลือกเทรนด์ที่มีรายละเอียดเชิงเทคนิคให้ชำแหละต่อได้
3. **Anti-Hype**: ข้ามข่าวที่มีลักษณะเป็น Clickbait หรือการปั่นราคาเหรียญ
4. **Insight Score Initial Check**: คัดกรองเฉพาะเรื่องที่คาดว่าจะมี Insight Score ≥ 4
"""

        user_prompt = f"""รวบรวมเทรนด์เทคโนโลยีที่น่าสนใจที่สุดในวันนี้ (Focus: AI, Tech, Crypto)
เพื่อนำไปเขียนในเพจ lookforward

ให้สรุปข้อมูลมาในรูปแบบ:
- ชื่อเทรนด์ (Technical Name)
- แหล่งที่มา (Primary Source)
- ข้อมูลสำคัญ (Fact/Numbers)
- เหตุผลที่ 'lookforward' ต้องนำเสนอ (Systemic Value)"""

        if self.ai:
            try:
                print_info("📡 Scouting for high-signal tech trends...")
                trends = self.ai.generate(user_prompt, system=system_prompt)
                if trends:
                    return trends.strip()
            except Exception as e:
                print_error(f"❌ Scouting failed: {e}")
        
        return "⚠️ ไม่พบเทรนด์ที่มีคุณภาพเพียงพอตามมาตรฐาน lookforward"

    def save_trends(self, trends: str):
        """Save the trend report."""
        output_dir = self.config.paths["research"] / get_date_str()
        ensure_dir(output_dir)
        
        filepath = output_dir / "daily_tech_trends.md"
        content = f"# Daily Tech Trends Report: {get_date_str()}\n"
        content += f"**Project**: lookforward (High-Signal Mode)  \n\n"
        content += "----- \n\n"
        content += trends
        
        save_markdown(content, filepath)
        print_success(f"✅ Tech Trends saved to: {filepath}")
        return filepath

def main():
    print_header("📡 LOOKFORWARD TECH SCOUT")
    researcher = TrendResearcher()
    trends = researcher.scan_sources()
    researcher.save_trends(trends)

if __name__ == "__main__":
    main()

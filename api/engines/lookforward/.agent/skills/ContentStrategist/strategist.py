#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContentStrategist - Tech Authority Edition for "lookforward"
Analyzes trends for systemic impact and technical depth.
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
    print_header, print_success, print_error, print_info, print_warning
)
from shared.config import get_config
from shared.ai_client import create_ai_client

class ContentStrategist:
    """
    Analyzes tech trends to create high-authority content strategies.
    """
    
    def __init__(self):
        self.config = get_config()
        self.logger = setup_logger(
            "ContentStrategist",
            self.config.paths["error_logs"] / f"{get_date_str()}_ContentStrategist.log"
        )
        self.ai = create_ai_client(self.logger)
    
    def analyze_trend(self, trend_data: str) -> str:
        """
        Deconstruct a trend to find the non-obvious systemic impact.
        CRITICAL: Strategy must provide foundation for Synthesis Framework.
        """
        system_prompt = f"""คุณคือ 'Lead Tech Strategist' ประจำเพจ lookforward
หน้าที่ของคุณคือการ 'ชำแหละ' ข่าวเทคโนโลยีเพื่อหาคุณค่าที่แท้จริง (Real Value) ไม่ใช่แค่กระแส (Hype)

🚨 กฎการวิเคราะห์ (Authority Blueprint):
1. **Facts First**: รวบรวมข้อเท็จจริงพื้นฐานก่อน (อะไร, เมื่อไหร่, ใคร, ทำไม)
2. **Systemic Impact**: วิเคราะห์ว่าสิ่งนี้กระทบต่อระบบนิเวศของ Tech/AI/Crypto อย่างไร
3. **Root Cause**: มองหาต้นเหตุที่แท้จริงที่ทำให้เกิดเทรนด์นี้
4. **Non-Obvious Angle**: หามุมมองที่คนส่วนใหญ่เข้าใจผิดหรือมองข้าม
5. **User-Centric**: คิดว่าผู้อ่านต้องการรู้อะไร? ได้ประโยชน์อะไร?
6. **Insight Score Check**: หากเทรนด์นี้ให้ Insight ไม่ถึงระดับ 4/5 ให้แจ้งว่า 'INSIGHT_LOW' เพื่อยกเลิก

⚠️ CRITICAL RULE: ห้ามกระโดดไป "ทำไม" ก่อนอธิบาย "อะไร"
- ผู้อ่านต้องเข้าใจ CONTEXT ก่อน (THE UPDATE)
- แล้วค่อยอธิบาย MECHANISM (TECH BREAKDOWN)
- จากนั้นค่อยวิเคราะห์ SYSTEMIC IMPACT

เป้าหมาย: วางโครงสร้างกลยุทธ์ที่ทำให้คนอ่านรู้สึกว่าได้รับความรู้ที่หาจากที่อื่นไม่ได้"""

        user_prompt = f"""วิเคราะห์ข้อมูลเทรนด์นี้และวางกลยุทธ์สำหรับเพจ lookforward:
---
{trend_data}
---

ให้ผลลัพธ์ในรูปแบบ Markdown ที่มีหัวข้อ (ตามลำดับนี้เท่านั้น):

## 1. Factual Foundation (ข้อเท็จจริงพื้นฐาน)
- **What**: เทคโนโลยี/ข่าวนี้คืออะไร? (1-2 ประโยค)
- **Who**: ใครทำ? บริษัทไหน? ทีมไหน?
- **When**: เปิดตัวเมื่อไหร่? (ถ้ามี)
- **Key Specs**: ข้อมูลสำคัญ (ราคา, performance, benchmarks)
- **Why Now**: ทำไมตอนนี้? ปัญหาอะไรที่มันแก้?

## 2. Technical Breakdown (กลไกเชิงเทคนิค)
- **How It Works**: อธิบายกลไกหลักแบบเข้าใจง่าย
- **Key Innovation**: นวัตกรรมหลักคืออะไร?
- **Comparison**: เทียบกับคู่แข่ง (ตาราง/bullet points)
- **Technical Depth**: รายละเอียดเชิงเทคนิคที่สำคัญ (3-5 ข้อ)

## 3. Non-Obvious Angle (มุมมองที่ไม่ธรรมดา)
- **What Most People See**: คนส่วนใหญ่เห็นอะไร? (misconception)
- **What's Actually Happening**: ความจริงเชิงระบบคืออะไร?
- **Systemic Connection**: เชื่อมโยงกับระบบใหญ่ยังไง? (monopoly, ecosystem, trend)
- **Root Cause**: ต้นเหตุที่แท้จริงคืออะไร? (โครงสร้างระบบ, เศรษฐศาสตร์, การเมือง)

## 4. Impact Analysis (ผลกระทบ)
- **Industry Impact**: กระทบอุตสาหกรรมยังไง?
- **User Impact**: ผู้ใช้ได้ประโยชน์/เสียหายยังไง?
- **Developer Impact**: นักพัฒนาควรรู้อะไร?
- **Startup Impact**: Startups ได้โอกาสอะไร?

## 5. Future Vision (มองไปข้างหน้า)
- **Short-term (3-6 months)**: จะเกิดอะไรขึ้นเร็วๆ นี้?
- **Long-term (1-2 years)**: แนวโน้มระยะยาว?
- **Contrarian Prediction**: ทำนายที่ขัดกับความเชื่อทั่วไป (ถ้ามี)
- **What to Watch**: ควรจับตาอะไรต่อ?

## 6. Content Strategy (กลยุทธ์การเขียน)
- **Hook Options**: เสนอ 3 แบบ (Contrarian, System Logic, Calm Disrupt)
- **Target Insight Score**: ประเมิน 1-5 (พร้อมเหตุผล)
- **Key Messages**: ข้อความหลักที่ต้องสื่อ (3-5 ข้อ)
- **Tone Guidance**: Calm & Sharp - เน้นอะไร? หลีกเลี่ยงอะไร?
- **Media Needs**: ต้องการ visual แบบไหน? (diagram, chart, screenshot)

⚠️ IMPORTANT: ถ้าเทรนด์นี้ไม่มีมุมมอง non-obvious หรือ systemic depth ให้ใส่ "INSIGHT_LOW" ที่ต้นไฟล์"""

        if self.ai:
            try:
                print_info("🧠 Analyzing trend for systemic impact...")
                analysis = self.ai.generate(user_prompt, system=system_prompt)
                if analysis:
                    return analysis.strip()
            except Exception as e:
                print_error(f"❌ Analysis failed: {e}")
        
        return "⚠️ ไม่สามารถวิเคราะห์ได้เนื่องจากข้อมูลไม่เพียงพอ"

    def save_strategy(self, analysis: str, topic: str):
        """Save the generated strategy to the project folder."""
        output_dir = self.config.paths["strategies"] / get_date_str()
        ensure_dir(output_dir)
        
        topic_safe = sanitize_filename(topic)
        filepath = output_dir / f"{topic_safe}.md"
        
        content = f"# Tech Content Strategy: {topic}\n\n"
        content += f"**Date**: {datetime.now().strftime('%Y-%m-%d')}  \n"
        content += f"**Focus**: lookforward Authority Mode  \n\n"
        content += "---\n\n"
        content += analysis
        
        save_markdown(content, filepath)
        print_success(f"✅ Strategy saved to: {filepath}")
        return filepath

def main():
    parser = argparse.ArgumentParser(description="Generate tech content strategy")
    parser.add_argument("--trend_file", help="Path to trend research file")
    parser.add_argument("--topic", help="Manually specify a topic to analyze")
    
    args = parser.parse_args()
    strategist = ContentStrategist()
    
    trend_content = ""
    topic = args.topic or "Tech Update"
    
    if args.trend_file:
        trend_content = load_markdown(args.trend_file)
    elif args.topic:
        trend_content = f"Analyze depth and future impact of: {args.topic}"
    else:
        print_error("Must provide --trend_file or --topic")
        return

    analysis = strategist.analyze_trend(trend_content)
    if "INSIGHT_LOW" in analysis:
        print_warning("🚫 Trend rejected: Insight density too low for lookforward standards.")
    else:
        strategist.save_strategy(analysis, topic)

if __name__ == "__main__":
    main()

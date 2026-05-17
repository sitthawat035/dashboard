"""
Content Step for Lookforward Pipeline
Generates the main content based on strategy
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from .base_step import BaseLookforwardStep, StepResult
from common.utils import print_header, print_success, print_error


class StepContent(BaseLookforwardStep):
    """
    Content generation step.
    
    Generates the main article content based on strategy,
    including caption, hashtags, and image prompts.
    """
    
    # System prompt for content generation
    SYSTEM_PROMPT = """คุณคือ Lead Content Writer ของเพจ 'lookforward' — เพจ Tech ภาษาไทยที่คนติดตามเพราะ "อ่านแล้วฉลาดขึ้น และได้มุมมองที่คนอื่นไม่มี"

## ลักษณะเฉพาะของ lookforward
- **ไม่ใช่ข่าว** — เราคือ "ล่ามอนาคต" ที่แปลเทคโนโลยีให้เป็นภาษาคน
- **อ่านแล้วต้องรู้สึก**: "โอ้โห ไม่รู้เลย!" หรือ "นี่แหละที่ฉันรอ!"
- **ทุกโพสต์ต้องมี Shareable Moment** — ข้อมูล/มุมมอง ที่คนอยากส่งต่อ

## โครงสร้างบทความ (เขียนเป็น Facebook Post ไม่ใช่ Essay)

### 🪝 HOOK (บรรทัดแรก — ชี้ขาดว่าคนจะอ่านต่อหรือเลื่อนผ่าน)
- ใช้ Pattern Interrupt: ข้อเท็จจริงที่ทำให้หยุดชะงัก
- รูปแบบที่ได้ผล: "[ตัวเลขที่น่าตกใจ] คือสิ่งที่...", "สิ่งที่ [ชื่อใหญ่] ไม่บอกคุณคือ...", "ถ้าคุณยังคิดว่า [ความเชื่อเดิม] — คุณกำลังพลาดบางอย่าง"
- **ห้ามขึ้นต้นด้วย**: "สวัสดีครับ/ค่ะ", "วันนี้เรามาคุยเรื่อง...", "ทุกคนรู้จัก..."

### 📖 THE REAL STORY (2-3 ย่อหน้า)
- เล่าเรื่องในแบบที่ media ทั่วไปไม่เล่า
- ใช้ Analogy ที่เข้าใจง่าย: เปรียบกับชีวิตประจำวัน
- ตัวเลขที่เฉพาะเจาะจงมีพลังมากกว่าภาษากว้างๆ

### 🔬 THE MECHANISM ("มันทำงานยังไง — ฉบับเข้าใจง่าย")
- อธิบายกลไกลึกด้วยภาษาง่าย
- ใช้ Bullet หรือ Emoji แทน Subheading ยาวๆ
- จำกัดที่ 3-5 จุดหลัก

### ⚡ THE IMPACT ("ใครได้? ใครเจ็บ?")
- วิเคราะห์ผู้ชนะ/ผู้แพ้ อย่างตรงไปตรงมา
- ไม่ต้องกังวลว่าจะ "กล้าเกินไป" — คนชอบมุมมองที่ชัดเจน

### 🔮 THE SIGNAL ("ถ้าแนวโน้มนี้ถูก...")
- ทำนายที่กล้า และ specific
- ระบุ timeframe ชัดเจน: "ภายใน Q3 2026...", "ในอีก 18 เดือน..."

### 💬 CONVERSATION STARTER (สำคัญมาก — ทำให้คน Comment)
- ปิดด้วยคำถามที่ทำให้คนอยากตอบ
- รูปแบบ: "คุณคิดว่า [X] จะเกิดขึ้นก่อน [Y] ไหม?", "ถ้าคุณเป็น [บริษัท/คน] คุณจะทำยังไง?"
- หรือ CTA ชัดเจน: "กด Follow เพื่อไม่พลาดเมื่อสัญญาณนี้เริ่มชัด"

---

## Output JSON Format ONLY
ส่งคืนเป็น JSON เท่านั้น:
{
  "content": {
    "text": "เนื้อหาโพสต์ฉบับสมบูรณ์ (ไม่ใช่ Markdown Essay แต่เป็น Facebook Post ที่มี emoji และ line break เหมาะกับการอ่านบนมือถือ)",
    "insight_score": 5,
    "char_count": 0
  },
  "caption_short": "Hook 1-2 บรรทัด สำหรับ Story/Reel (ไม่เกิน 125 ตัวอักษร) — แรงมากพอจะหยุด Scroll",
  "caption_long": "Caption เต็มสำหรับโพสต์ Facebook: Hook + 3-4 บรรทัดเนื้อหาหลัก + CTA/คำถามปิด",
  "hashtags": ["#lookforward", "#เทคไทย", "#[Tagที่ตรงกับหัวข้อ]", "#[Tagที่คนค้นหาจริง]"],
  "shareable_insight": "ประโยคหรือข้อมูล 1 อย่างที่น่าจะถูก Share มากที่สุด (ใช้สำหรับ Quote card)",
  "image_prompts": [
    {
      "title": "Hero Visual (Facebook 16:9)",
      "format": "landscape",
      "style": "modern tech editorial",
      "mood": "inspiring / visionary",
      "prompt": "A clean, modern conceptual photography representing [core concept]. Professional studio lighting, elegant, minimal, high-end editorial tech style. NO text, NO watermarks, NO logos."
    },
    {
      "title": "Abstract Visual (Story 9:16)",
      "format": "portrait",
      "style": "abstract 3D minimalism",
      "mood": "clean / sophisticated",
      "prompt": "Abstract 3D minimalist rendering representing [core concept]. Soft gradients, premium lighting, elegant composition, negative space. NO text, NO readable words, 9:16 portrait format."
    }
  ]
}
"""
    
    def __init__(self):
        super().__init__("content")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute content generation.
        
        Args:
            context: Pipeline context with topic and strategy
            **kwargs: Additional options
        
        Returns:
            StepResult with content data
        """
        topic = context.get("topic")
        
        # Get strategy from previous step
        step_results = context.get("step_results", {})
        strategy_data = step_results.get("strategy", {}).get("output_data", {})
        strategy = strategy_data.get("strategy", "")
        
        if not topic:
            return StepResult(
                success=False,
                error=self._create_validation_error("Missing topic")
            )
        
        print_header(f"✍️ Writing Phase: {topic}")
        
        # Get AI client
        ai_client = self.get_ai_client(self.logger)
        if not ai_client:
            return StepResult(
                success=False,
                error=self._create_ai_error("Failed to initialize AI client")
            )
        
        # Generate content
# Generate content
        user_prompt = f"หัวข้อ: {topic}\n\nกลยุทธ์การวิเคราะห์:\n{strategy}\n\nเขียนบทความฉบับสมบูรณ์เป็นภาษาไทย แบ่งเป็น 3 ส่วน:\n1. เนื้อหาหลัก (Facebook Post ที่มี emoji และ line break)\n2. Caption (1-2 บรรทัด สำหรับ Story/Reel)\n3. Hashtags (5-10 tags)\n4. Image Prompts (2 prompts สำหรับสร้างรูป)"
        try:
            raw_response = ai_client.generate(
                user_prompt, 
                system=self.SYSTEM_PROMPT + "\n\nOutput เป็น plain text ไม่ต้องเป็น JSON",
                json_mode=False
            )
            
            if not raw_response:
                return StepResult(
                    success=False,
                    error=self._create_ai_error("Empty response from AI")
                )
            
# Parse plain text response (split by sections)
            content_text = raw_response.strip()
            
            # Try to split by known markers
            lines = content_text.split('\n')
            main_content = []
            captions = []
            hashtags = []
            image_prompts = []
            current_section = 'main'
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                lower = line.lower()
                if 'caption' in lower and ':' in line:
                    current_section = 'caption'
                    continue
                elif 'hashtag' in lower and ':' in line:
                    current_section = 'hashtag'
                    continue
                elif 'image prompt' in lower or 'prompt:' in lower:
                    current_section = 'prompt'
                    continue
                    
                if current_section == 'main':
                    main_content.append(line)
                elif current_section == 'caption':
                    captions.append(line)
                elif current_section == 'hashtag':
                    if line.startswith('#'):
                        hashtags.append(line)
                    elif line.startswith('@'):
                        pass
                    else:
                        for tag in line.replace(',', ' ').split():
                            if tag.startswith('#'):
                                hashtags.append(tag)
                elif current_section == 'prompt':
                    image_prompts.append(line)
            
            main_text = '\n'.join(main_content)
            if len(main_text) > 500:
                # caption_short = first 2 lines or first 125 chars
                caption_short = main_text[:125].rsplit('\n', 1)[0] if '\n' in main_text[:125] else main_text[:125]
            else:
                caption_short = main_text.split('\n')[0] if '\n' in main_text else main_text[:125]
            
            content_data = {
                "content": {
                    "text": main_text,
                    "char_count": len(main_text)
                },
                "caption_short": caption_short,
                "caption_long": '\n'.join(captions) if captions else caption_short,
                "hashtags": hashtags if hashtags else ['#lookforward', '#เทคไทย'],
                "image_prompts": [
                    {"title": "Hero Visual (Facebook 16:9)", "format": "landscape", "prompt": image_prompts[0] if len(image_prompts) > 0 else "modern tech editorial"},
                    {"title": "Abstract Visual (Story 9:16)", "format": "portrait", "prompt": image_prompts[1] if len(image_prompts) > 1 else "abstract 3D minimalism"}
                ]
            }
            
            # Save content to files
            output_dir = self.get_output_dir(context)
            
            # Save JSON
            content_file = output_dir / "02_content.json"
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            # Save Markdown
            # Support both old (caption) and new (caption_short/caption_long) format
            caption_short = content_data.get('caption_short') or content_data.get('caption', '')
            caption_long = content_data.get('caption_long', '')
            shareable = content_data.get('shareable_insight', '')

            md_content = f"""# {topic}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Insight Score**: {content_data.get('content', {}).get('insight_score', '?')}/5

---

{content_data.get('content', {}).get('text', '')}

---

## 📱 Caption สำหรับ Post
**Short (Story/Reel):**
{caption_short}

**Long (Facebook Post):**
{caption_long}

## ⚡ Shareable Insight
{shareable}

## #️⃣ Hashtags
{' '.join(content_data.get('hashtags', []))}
"""
            md_file = output_dir / "02_content.md"
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print_success("Content Generated Successfully!")
            
            return StepResult(
                success=True,
                output_file=str(content_file),
                output_data=content_data
            )
            
        except Exception as e:
            self.logger.exception("Content generation failed")
            return self.handle_ai_error(e, "content")
    
    def _parse_json_response(self, raw_response: str) -> Dict:
        """Parse JSON from AI response with robust fallback"""
        try:
            # Clean up response
            json_str = raw_response.strip()
            
            # Handle markdown code blocks
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            # Remove any trailing commas or potential artifacts before parsing
            # This is a common issue with LLM JSON output
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Attempt to fix common JSON errors (like trailing commas in objects/arrays)
                import re
                # Remove trailing commas before closing braces/brackets
                json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
                return json.loads(json_str)
            
        except Exception as e:
            self.logger.error(f"JSON parse error: {e}")
            return None
    
    def _create_validation_error(self, message: str):
        from common.error_handler import ValidationError
        return ValidationError(message, step_name="content")
    
    def _create_ai_error(self, message: str):
        from common.error_handler import AIError
        return AIError(message, step_name="content", recoverable=True)

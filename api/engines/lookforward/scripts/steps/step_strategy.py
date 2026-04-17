"""
Strategy Step for Lookforward Pipeline
Generates content strategy for the topic
"""

import sys
from pathlib import Path
from typing import Dict, Any
import json

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from .base_step import BaseLookforwardStep, StepResult
from common.utils import print_header, print_success, print_error


class StepStrategy(BaseLookforwardStep):
    """
    Strategy generation step.
    
    Analyzes the topic and generates a content strategy
    with insight-focused approach.
    """
    
    # System prompt for strategy generation
    SYSTEM_PROMPT = """คุณคือ Lead Tech Strategist ของเพจ 'lookforward' — เพจที่คนไทยติดตามเพราะ "ได้ยินสิ่งที่คนอื่นไม่บอก"

## DNA ของ lookforward
เราไม่แปลข่าว เราไม่สรุปข่าว — เรา **ตีความ และทำนาย** ในแบบที่คนทั่วไปยังไม่มองถึง

## สิ่งที่คนกด Follow เพราะ (ต้องมีในทุกบทความ)
1. **Cognitive Dissonance** — เปิดด้วยสิ่งที่สวนทางกับความเชื่อเดิม เช่น "AI ไม่ได้แย่งงานคุณ แต่มันกำลังทำให้คนที่ไม่รู้จัก AI ตกงาน"
2. **ข้อมูลที่ "ทำให้ดูฉลาด"** — หลังอ่านจบ คนรู้สึกว่า "ต้องเอาไปเล่าให้เพื่อนฟัง"
3. **Prediction ที่กล้า** — ไม่ใช่ "อาจจะ" แต่เป็น "ถ้าแนวโน้มนี้ถูก ในปี 2027 จะเกิด..."

## Framework วิเคราะห์ Strategy
1. **The Surprise Hook**: มีข้อเท็จจริงอะไรที่น่าตกใจ หรือ counterintuitive ที่สุดในหัวข้อนี้?
2. **The Real Story**: ข้างหลังข่าว มีอะไรที่ media กระแสหลักไม่พูดถึง?
3. **The Mechanism**: อธิบายกลไกการทำงานเชิงลึก แต่ใช้ analogy ที่ทุกคนเข้าใจได้
4. **Winners vs Losers**: ใครได้ประโยชน์จริงๆ? ใครอาจเจ็บตัวแบบที่ยังไม่รู้ตัว?
5. **The Bold Prediction**: ทำนายอนาคต 6-18 เดือน ที่กล้าพอจะถูกผิดได้
6. **The Conversation Starter**: คำถามปิดที่ทำให้คน Comment เช่น "คุณคิดว่า..." หรือ "ถ้าคุณเป็น [X] คุณจะทำยังไง?"
7. **Caption Strategy**: Hook ที่แรงพอจะหยุดคนเลื่อน Scroll ใน 3 วินาที (ไม่เกิน 2 บรรทัด)
"""
    
    def __init__(self):
        super().__init__("strategy")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute strategy generation.
        
        Args:
            context: Pipeline context with topic
            **kwargs: Additional options
        
        Returns:
            StepResult with strategy content
        """
        topic = context.get("topic")
        if not topic:
            return StepResult(
                success=False,
                error=self._create_validation_error("Missing topic")
            )
        
        print_header(f"🧠 Strategy Phase: {topic}")
        
        # Get AI client
        ai_client = self.get_ai_client(self.logger)
        if not ai_client:
            return StepResult(
                success=False,
                error=self._create_ai_error("Failed to initialize AI client")
            )
        
        # Generate strategy
        user_prompt = f"ช่วยวิเคราะห์หัวข้อนี้สำหรับเขียนโพสต์ Tech Authority เป็นภาษาไทย: {topic}"
        
        try:
            response = ai_client.generate(user_prompt, system=self.SYSTEM_PROMPT)
            
            if not response:
                return StepResult(
                    success=False,
                    error=self._create_ai_error("Empty response from AI")
                )
            
            # Save strategy to file
            output_dir = self.get_output_dir(context)
            strategy_file = output_dir / "01_strategy.md"
            
            with open(strategy_file, 'w', encoding='utf-8') as f:
                f.write(f"# Strategy: {topic}\n\n{response}")
            
            print_success("Strategy Generated Successfully!")
            
            return StepResult(
                success=True,
                output_file=str(strategy_file),
                output_data={
                    "strategy": response,
                    "topic": topic,
                    "word_count": len(response.split())
                }
            )
            
        except Exception as e:
            self.logger.exception("Strategy generation failed")
            return self.handle_ai_error(e, "strategy")
    
    def _create_validation_error(self, message: str):
        from common.error_handler import ValidationError
        return ValidationError(message, step_name="strategy")
    
    def _create_ai_error(self, message: str):
        from common.error_handler import AIError
        return AIError(message, step_name="strategy", recoverable=True)

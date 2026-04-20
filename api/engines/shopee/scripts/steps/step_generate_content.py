"""
Generate Content Step for Shopee Affiliate Pipeline
AI-powered caption generation
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from .base_step import BaseAffiliateStep, StepResult
from common.utils import print_header, print_success, print_error, print_warning


class StepGenerateContent(BaseAffiliateStep):
    """
    Content generation step.
    
    Generates captions for selected products using AI.
    """
    
    SYSTEM_PROMPT = """คุณคือเพื่อนสายป้ายยาสินค้า Shopee ที่เขียน caption แบบสนุก จริงใจ และดึงดูดคนคลิก
เป้าหมาย: ทำให้คนอยากช้อปทันที!

สไตล์:
- Hook แรงในบรรทัดแรก (ตั้งคำถาม / บอกราคาถูก / บอกว่าดีมาก)
- บอกจุดเด่น 1-2 จุดสั้นๆ พร้อมอิโมจิ 🔥✨💸😍
- ปิดด้วย CTA ชัดเจน เช่น "จิ้มลิงก์เลยนะ!" หรือ "รีบจับก่อนหมด!"
- ลิงก์ให้เขียนว่า [LINK] เท่านั้น (ห้ามใช้ชื่ออื่น)
- hashtag 3-5 อันที่เกี่ยวกับสินค้า

ตอบเป็น JSON เท่านั้น:
{"caption": "แคปชั่นเต็ม...", "hashtags": ["tag1", "tag2"]}
"""

    
    def __init__(self):
        super().__init__("generate_content")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute content generation.
        
        Args:
            context: Pipeline context with selected products
            **kwargs: Additional options
        
        Returns:
            StepResult with generated content
        """
        # Ensure UTF-8 output for Windows
        if sys.platform == "win32":
            import io
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding='utf-8')
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding='utf-8')

        # Get selected products from previous step
        step_results = context.get("step_results", {})
        select_data = step_results.get("select_products", {}).get("output_data", {})
        products = select_data.get("selected_products", [])
        
        if not products:
            return StepResult(
                success=False,
                error=self._create_validation_error("No products to generate content for")
            )
        
        print_header(f"[AI] Generating Captions for {len(products)} Products")
        
        # Get AI client
        ai_client = self.get_ai_client(self.logger)
        if not ai_client:
            return StepResult(
                success=False,
                error=self._create_ai_error("AI client not available")
            )
        
        generated_content = []
        
        for i, product in enumerate(products):
            print(f"\n  [{i+1}/{len(products)}] {product['name'][:40]}...")
            
            user_prompt = f"""สินค้า: {product['name']}
ราคา: {product['original_price']}
ราคาโปรโมชั่น: {product.get('discount_price', product['original_price'])}
รางวัล: {product.get('coins', 'N/A')}
ลิงก์: {product['url']}

เขียนแคปชั่นสั้นๆ กระชับ ไม่เกิน 5 บรรทัด!"""
            
            try:
                raw_response = ai_client.generate(user_prompt, system=self.SYSTEM_PROMPT)
                
                if raw_response:
                    # Parse JSON
                    json_str = raw_response
                    if "```json" in raw_response:
                        json_str = raw_response.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_response:
                        json_str = raw_response.split("```")[1].split("```")[0].strip()
                    
                    data = json.loads(json_str)
                    
                    generated_content.append({
                        "product": product,
                        "caption": data.get("caption", ""),
                        "hashtags": data.get("hashtags", []),
                        "raw_response": raw_response
                    })
                    print_success("  ✓ Generated")
                else:
                    # Fallback caption
                    fallback = self._create_fallback_caption(product)
                    generated_content.append({
                        "product": product,
                        "caption": fallback["caption"],
                        "hashtags": fallback["hashtags"],
                        "raw_response": None
                    })
                    print_warning("  ⚠ Using fallback")
                    
            except Exception as e:
                self.logger.error(f"Content generation failed for {product['name']}: {e}")
                # Fallback caption
                fallback = self._create_fallback_caption(product)
                generated_content.append({
                    "product": product,
                    "caption": fallback["caption"],
                    "hashtags": fallback["hashtags"],
                    "raw_response": None,
                    "error": str(e)
                })
                print_warning(f"  ⚠ Error: {e}")
        
        print_success(f"\nGenerated {len(generated_content)} captions")
        
        return StepResult(
            success=True,
            output_data={
                "generated_content": generated_content,
                "total_count": len(generated_content)
            }
        )
    
    def _create_fallback_caption(self, product: Dict) -> Dict:
        """Create a simple fallback caption"""
        name = product.get("name", "สินค้า")
        price = product.get("original_price", "N/A")
        url = product.get("url", "")
        
        caption = f"""🧴 {name}
💰 ราคา: {price}
🔗 ลิงก์: [LINK]"""
        
        hashtags = ["shopee", "beauty", "skincare"]
        
        return {"caption": caption, "hashtags": hashtags}
    
    def _create_validation_error(self, message: str):
        from common.error_handler import ValidationError
        return ValidationError(message, step_name="generate_content")
    
    def _create_ai_error(self, message: str):
        from common.error_handler import AIError
        return AIError(message, step_name="generate_content")

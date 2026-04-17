"""
Select Products Step for Shopee Affiliate Pipeline
AI-powered product selection
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
from common_shared.utils import print_header, print_success, print_error, print_warning


class StepSelectProducts(BaseAffiliateStep):
    """
    Product selection step.
    
    Uses AI to select the best products for posting.
    """
    
    SYSTEM_PROMPT = """คุณคือ Senior Merchandiser ของ Shopee Affiliate
หน้าที่คือคัดเลือกสินค้า "ตัวเด็ด" ประจำวัน 4 ชิ้น (เช้า, เที่ยง, เย็น, ดึก)
เกณฑ์การเลือก:
1. น่าสนใจ: ชื่อเสียงดี หรือแก้ปัญหาผิวได้จริง
2. หลากหลาย: ไม่ใช่ครีมอย่างเดียว ควรมีกันแดด, โฟม, มาส์ก
3. คุ้มค่า: ราคาไม่แพง (< 500 บาท)

ตอบเป็น JSON:
{
  "selected_indices": [1, 5, 8, 12],
  "reason": "เหตุผลสั้นๆ"
}
"""
    
    def __init__(self):
        super().__init__("select_products")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute product selection.
        
        Args:
            context: Pipeline context with loaded products
            **kwargs: Additional options
                - count: Number of products to select (default: 4)
        
        Returns:
            StepResult with selected products
        """
        options = context.get("options", {})
        count = options.get("count", kwargs.get("count", 4))
        
        # Get products from previous step
        step_results = context.get("step_results", {})
        load_data = step_results.get("load_products", {}).get("output_data", {})
        products = load_data.get("products", [])
        
        if not products:
            return StepResult(
                success=False,
                error=self._create_validation_error("No products to select from")
            )
        
        print_header(f"[AI] Selecting Top {count} from {len(products)} Items")
        
        # If not enough products, return all
        if len(products) <= count:
            print_warning(f"Only {len(products)} products available, using all")
            return StepResult(
                success=True,
                output_data={
                    "selected_products": products,
                    "selection_method": "all_available"
                }
            )
        
        # Get AI client
        ai_client = self.get_ai_client(self.logger)
        if not ai_client:
            # Fallback: use first N products
            print_warning("AI client not available, using first products")
            return StepResult(
                success=True,
                output_data={
                    "selected_products": products[:count],
                    "selection_method": "fallback"
                }
            )
        
        # Prepare list for AI (limit to first 40 items)
        items_str = ""
        for i, p in enumerate(products[:40]):
            items_str += f"{i+1}. {p['name']} ({p['original_price']})\n"
        
        user_prompt = f"รายการสินค้า:\n{items_str}\n\nเลือก {count} ชิ้นที่ดีที่สุดสำหรับวันนี้!"
        
        try:
            raw_response = ai_client.generate(user_prompt, system=self.SYSTEM_PROMPT)
            
            if not raw_response:
                return StepResult(
                    success=True,
                    output_data={
                        "selected_products": products[:count],
                        "selection_method": "fallback_no_response"
                    }
                )
            
            # Parse JSON
            json_str = raw_response
            if "```json" in raw_response:
                json_str = raw_response.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_response:
                json_str = raw_response.split("```")[1].split("```")[0].strip()
            
            data = json.loads(json_str)
            indices = [i-1 for i in data.get("selected_indices", [])]  # Convert to 0-based
            
            selected = []
            for idx in indices:
                if 0 <= idx < len(products):
                    selected.append(products[idx])
            
            # Fallback if selection failed
            if not selected:
                selected = products[:count]
            
            print_success(f"Selected {len(selected)} items to post.")
            
            return StepResult(
                success=True,
                output_data={
                    "selected_products": selected,
                    "selection_method": "ai",
                    "ai_reason": data.get("reason", "")
                }
            )
            
        except Exception as e:
            self.logger.error(f"AI selection failed: {e}")
            print_warning(f"AI selection failed, using fallback")
            return StepResult(
                success=True,
                output_data={
                    "selected_products": products[:count],
                    "selection_method": "fallback_error"
                }
            )
    
    def _create_validation_error(self, message: str):
        from common_shared.error_handler import ValidationError
        return ValidationError(message, step_name="select_products")

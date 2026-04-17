"""
Step: Publish to Facebook (Shopee Affiliate)
Automatically posts the generated product review content and images to a Facebook Page.
"""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from common_shared.pipeline_base import StepResult
from common_shared.utils import print_header, print_info, print_success, print_error

# Use the centralized facebook API we created earlier
import sys
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
from common.facebook_api import post_to_facebook

from .base_step import BaseAffiliateStep

class StepPublishFb(BaseAffiliateStep):
    """
    Publish shoppable affiliate content to Facebook.
    Expects input from step_ready_to_post.
    """
    
    def __init__(self):
        super().__init__(name="publish_fb")
        
    def execute(self, context: Dict[str, Any]) -> StepResult:
        """
        Execute the publish step. Shopee base doesn't pass 'previous_result' to _execute,
        it uses the standard API where context contains step_results.
        """
        print_header("🚀 Publishing Phase: Auto-Post to Facebook (Pai-ya)")
        
        # Load environment variables just to be safe
        load_dotenv(self.root_dir / ".env")
        
        page_id = os.environ.get("SHOPEE_PAGE_ID")
        access_token = os.environ.get("SHOPEE_PAGE_TOKEN")
        
        if not page_id or not access_token:
            msg = "SHOPEE_PAGE_ID or SHOPEE_PAGE_TOKEN not found in .env. Skipping auto-publish."
            print_error(f"⚠️ {msg}")
            return StepResult(success=True, output_data={"published": False, "reason": msg})
            
        step_results = context.get("step_results", {})
        ready_data = step_results.get("ready_to_post", {}).get("output_data", {})
        
        package_path = ready_data.get("output_dir")
        
        if not package_path:
            print_error("❌ Could not find package_path from previous step.")
            return StepResult(success=False, error=Exception("Missing content to publish."))
            
        package_dir = Path(package_path)
        post_file = package_dir / "post.txt"
        
        if not post_file.exists():
            msg = f"Failed to find post content at: {post_file}"
            print_error(f"❌ {msg}")
            return StepResult(success=False, error=Exception(msg))
            
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                message = f.read().strip()
        except Exception as e:
            msg = f"Failed to read post content: {e}"
            print_error(f"❌ {msg}")
            return StepResult(success=False, error=Exception(msg))
            
        # Find image to attach
        image_path = None
        images_dir = package_dir / "images"
        if images_dir.exists() and images_dir.is_dir():
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                images = list(images_dir.glob(f"*{ext}"))
                if images:
                    # Shopee posts might have collages or multiple images, we pick the first or combined one.
                    # Usually "collage.jpg" if it exists, else just the first item.
                    collage = images_dir / "collage.jpg"
                    if collage.exists():
                        image_path = str(collage)
                    else:
                        image_path = str(images[0])
                    break
                    
        print_info(f"Preparing to publish to Pai-ya Page ID: {page_id}")
        if image_path:
            print_info(f"Attaching media: {Path(image_path).name}")
        else:
            print_info("No media attached (Text only)")
            
        # Call Graph API
        result = post_to_facebook(
            page_id=page_id,
            access_token=access_token,
            message=message,
            image_path=image_path
        )
        
        if result.get("success"):
            return StepResult(
                success=True,
                output_data={
                    "published": True,
                    "platform": "facebook",
                    "post_id": result.get("data", {}).get("id")
                }
            )
        else:
            return StepResult(
                success=False,
                error=Exception(result.get("error"))
            )

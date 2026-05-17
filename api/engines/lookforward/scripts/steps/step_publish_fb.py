"""
Step: Publish to Facebook
Automatically posts the generated content and image to a Facebook Page.
"""

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from common.pipeline_base import StepResult
from common.utils import print_header, print_info, print_success, print_error
from common.facebook_api import post_to_facebook
from .base_step import BaseLookforwardStep

class StepPublishFb(BaseLookforwardStep):
    """
    Publish content to Facebook.
    Expects input from step_ready_to_post.
    """
    
    def __init__(self):
        super().__init__(name="publish_fb")
        
    def execute(self, context: Dict[str, Any], **kwargs) -> StepResult:
        """
        Satisfy BaseStep abstract contract.
        Retrieves previous step output from context and delegates to _execute().
        """
        previous_result = context.get("step_results", {}).get("ready_to_post", {}).get("output_data", {})
        return self._execute(context, previous_result)

    def _execute(self, context: Dict[str, Any], previous_result: Dict[str, Any]) -> StepResult:
        """
        Execute the publish step.
        """

        print_header("🚀 Publishing Phase: Auto-Post to Facebook")
        
        # Load environment variables just to be safe
        load_dotenv(self.root_dir / ".env")
        
        page_id = os.environ.get("FACEBOOK_PAGE_ID")
        access_token = os.environ.get("FACEBOOK_PAGE_TOKEN")
        
        if not page_id or not access_token:
            msg = "FACEBOOK_PAGE_ID or FACEBOOK_PAGE_TOKEN not found in .env. Skipping auto-publish."
            print_error(f"⚠️ {msg}")
            # Do not fail the pipeline if it's just missing credentials
            return StepResult(success=True, output_data={"published": False, "reason": msg})
            
        # Get data from ready_to_post step
        package_path = previous_result.get("package_path")
        post_file = previous_result.get("post_file")
        
        if not package_path or not post_file:
            # Fallback to looking in context if not in previous result
            print_error("❌ Could not find package_path or post_file from previous step.")
            return StepResult(success=False, error=Exception("Missing content to publish."))
            
        # Read the message content
        try:
            with open(post_file, 'r', encoding='utf-8') as f:
                message = f.read().strip()
        except Exception as e:
            msg = f"Failed to read post content: {e}"
            print_error(f"❌ {msg}")
            return StepResult(success=False, error=Exception(msg))
            
        # Find image to attach
        image_path = None
        media_dir = Path(package_path) / "media"
        if media_dir.exists() and media_dir.is_dir():
            # Find the first image file
            for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                images = list(media_dir.glob(f"*{ext}"))
                if images:
                    image_path = str(images[0])
                    break
                    
        print_info(f"Preparing to publish to Facebook Page ID: {page_id}")
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
            # We return success=False so the pipeline knows it failed the publish step
            # but the files are already generated.
            return StepResult(
                success=False,
                error=Exception(result.get("error"))
            )

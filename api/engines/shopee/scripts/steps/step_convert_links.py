"""
Convert Links Step for Shopee Affiliate Pipeline
Converts product URLs to affiliate links
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from .base_step import BaseAffiliateStep, StepResult
from common_shared.utils import print_header, print_success, print_error, print_warning


class StepConvertLinks(BaseAffiliateStep):
    """
    Affiliate link conversion step.
    
    Converts Shopee product URLs to affiliate links.
    """
    
    def __init__(self):
        super().__init__("convert_links")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute link conversion.
        
        Args:
            context: Pipeline context with downloaded content
            **kwargs: Additional options
                - affiliate_id: Shopee affiliate ID (from env or config)
        
        Returns:
            StepResult with converted affiliate links
        """
        # Get downloaded content from previous step
        step_results = context.get("step_results", {})
        download_data = step_results.get("download_images", {}).get("output_data", {})
        downloaded_content = download_data.get("downloaded_content", [])
        
        if not downloaded_content:
            return StepResult(
                success=False,
                error=self._create_validation_error("No content to convert links for")
            )
        
        print_header("Converting to Affiliate Links")
        
        # Get affiliate ID from env or config
        affiliate_id = os.getenv("SHOPEE_AFFILIATE_ID", "")
        if not affiliate_id:
            # Try to get from .env file
            env_file = project_root / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("SHOPEE_AFFILIATE_ID"):
                            affiliate_id = line.split("=")[1].strip().strip('"')
                            break
        
        if not affiliate_id:
            print_warning("No SHOPEE_AFFILIATE_ID found, using placeholder")
            affiliate_id = "YOUR_AFFILIATE_ID"
        
        print(f"  Affiliate ID: {affiliate_id}")
        
        converted_content = []
        total_converted = 0
        
        # Prepare links for conversion
        links_to_convert = []
        valid_items = []
        
        for i, item in enumerate(downloaded_content):
            product = item.get("product", {})
            original_url = product.get("url", "")
            product_name = product.get("name", "unknown")
            
            print(f"\n  [{i+1}/{len(downloaded_content)}] {product_name[:40]}...")
            
            if not original_url:
                print_warning("  No URL, skipping")
                converted_content.append({
                    **item,
                    "affiliate_url": None,
                    "link_error": "No original URL"
                })
                continue
            
            links_to_convert.append(original_url)
            valid_items.append(item)
            
        if links_to_convert:
            try:
                # Import the Playwright converter
                from shopee_affiliate.tools.convert_affiliate_links import convert_links
                
                print("\n🌐 Connecting to Playwright for Affiliate Links Conversion (Make sure Chrome is running on port 9222)")
                affiliate_links = convert_links(
                    links=links_to_convert,
                    affiliate_id=affiliate_id,
                    use_browser=True,
                    cdp_url="http://localhost:9222",
                    headless=False
                )
                
                for idx, (original_url, item) in enumerate(zip(links_to_convert, valid_items)):
                    # affiliate_links may not match length if catastrophic failure, safe access
                    if idx < len(affiliate_links) and affiliate_links[idx] and affiliate_links[idx] != original_url:
                        print_success(f"  Converted! -> {affiliate_links[idx]}")
                        total_converted += 1
                        converted_content.append({
                            **item,
                            "affiliate_url": affiliate_links[idx],
                            "original_url": original_url
                        })
                    else:
                        print_warning(f"  Conversion Failed/Fallback. Kept original URL.")
                        converted_content.append({
                            **item,
                            "affiliate_url": original_url,
                            "original_url": original_url,
                            "link_error": "Playwright conversion failed or returned original link"
                        })
            
            except Exception as e:
                self.logger.error(f"Link batch conversion failed: {e}")
                print_error(f"  Error calling Playwright Convert Links: {e}")
                
                # Fallback on error
                for original_url, item in zip(links_to_convert, valid_items):
                    converted_content.append({
                        **item,
                        "affiliate_url": original_url,
                        "original_url": original_url,
                        "link_error": str(e)
                    })
        
        print_success(f"\nConverted {total_converted}/{len(downloaded_content)} links")
        
        return StepResult(
            success=True,
            output_data={
                "converted_content": converted_content,
                "total_converted": total_converted,
                "affiliate_id": affiliate_id
            }
        )
    
    def _create_validation_error(self, message: str):
        from common_shared.error_handler import ValidationError
        return ValidationError(message, step_name="convert_links")
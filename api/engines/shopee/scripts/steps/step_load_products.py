"""
Load Products Step for Shopee Affiliate Pipeline
Loads products from CSV or manual input
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from .base_step import BaseAffiliateStep, StepResult
from common.utils import print_header, print_success, print_error, print_info


class StepLoadProducts(BaseAffiliateStep):
    """
    Load products step.
    
    Loads products from:
    1. CSV file in ScrapedData (priority)
    2. Manual input template (fallback)
    """
    
    def __init__(self):
        super().__init__("load_products")
    
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute product loading.
        
        Args:
            context: Pipeline context
            **kwargs: Additional options
                - max_price: Maximum price filter (default: 500)
                - csv_file: Specific CSV file path (optional)
        
        Returns:
            StepResult with loaded products
        """
        options = context.get("options", {})
        max_price = options.get("max_price", kwargs.get("max_price", 500))
        csv_file = options.get("csv_file", kwargs.get("csv_file"))
        
        print_header("📂 Loading Products")
        
        products = []
        
        # Try CSV first
        if csv_file:
            csv_path = Path(csv_file)
            products = self.load_products_from_csv(csv_path, max_price)
            print_info(f"Loaded from specified CSV: {csv_path.name}")
        else:
            # Find latest CSV
            latest_csv = self.get_latest_csv()
            if latest_csv:
                products = self.load_products_from_csv(latest_csv, max_price)
                print_info(f"Loaded from latest CSV: {latest_csv.name}")
        
        # Fallback to manual input
        if not products:
            manual_file = self.project_root / "product_input_template.md"
            if manual_file.exists():
                products = self.load_products_from_markdown(manual_file)
                print_info("Loaded from manual input template")
        
        if not products:
            print_error("No products found!")
            print_info(f"Scraped Dir: {self.scraped_dir}")
            print_info(f"Manual Path: {self.project_root / 'product_input_template.md'}")
            return StepResult(
                success=False,
                error=self._create_validation_error("No products found")
            )
        
        print_success(f"Found {len(products)} products (max price: ฿{max_price})")
        
        return StepResult(
            success=True,
            output_data={
                "products": products,
                "total_count": len(products),
                "max_price": max_price
            }
        )
    
    def _create_validation_error(self, message: str):
        from common.error_handler import ValidationError
        return ValidationError(message, step_name="load_products")

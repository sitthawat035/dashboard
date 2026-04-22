"""
Shopee Affiliate Pipeline Controller
Main pipeline orchestration with CLI support
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from common.pipeline_base import BasePipeline, PipelineMode, StepResult
from common.utils import setup_logger, print_header, print_success, print_error, print_info
from common.state_manager import StateManager
from common.error_handler import ErrorHandler, ErrorSeverity

from steps import (
    StepLoadProducts,
    StepSelectProducts,
    StepGenerateContent,
    StepDownloadImages,
    StepConvertLinks,
    StepReadyToPost,
    StepPublishFb
)


class AffiliatePipeline(BasePipeline):
    """
    Shopee Affiliate Pipeline Controller.
    
    Pipeline Steps:
    1. Load Products - Load products from CSV or manual input
    2. Select Products - AI-powered product selection
    3. Generate Content - AI-powered caption generation
    4. Download Images - Download product images
    5. Convert Links - Convert to affiliate links
    6. Ready to Post - Package for posting
    """
    
    PIPELINE_NAME = "shopee_affiliate"
    
    def __init__(
        self,
        mode: str = "full",
        output_dir: Optional[Path] = None,
        state_manager: Optional[StateManager] = None
    ):
        """
        Initialize Affiliate Pipeline.
        
        Args:
            mode: Pipeline mode (full, quick, content-only, resume, dry-run)
            output_dir: Output directory for generated content
            state_manager: State manager instance
        """
        # Initialize base pipeline
        super().__init__(
            project_root=project_root,
            project_id=self.PIPELINE_NAME
        )
        
        self.mode = mode
        self.output_dir = output_dir or project_root / "data"
        self.run_id = self._generate_run_id()
        
        # Override state manager if provided
        if state_manager:
            self.state = state_manager
        
        # Initialize steps
        self.steps = {
            "load_products": StepLoadProducts(),
            "select_products": StepSelectProducts(),
            "generate_content": StepGenerateContent(),
            "download_images": StepDownloadImages(),
            "convert_links": StepConvertLinks(),
            "ready_to_post": StepReadyToPost(),
            "publish_fb": StepPublishFb()
        }
        
        # Step order for different modes
        self.step_order = {
            "full": [
                "load_products",
                "select_products", 
                "generate_content",
                "download_images",
                "convert_links",
                "ready_to_post",
                "publish_fb"
            ],
            "quick": [
                "load_products",
                "select_products",
                "generate_content",
                "ready_to_post",
                "publish_fb"
            ],
            "content-only": [
                "load_products",
                "select_products",
                "generate_content"
            ],
            "links-only": [
                "load_products",
                "convert_links"
            ]
        }
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run(
        self,
        topic: Optional[str] = None,
        count: int = 4,
        max_price: int = 500,
        csv_file: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the affiliate pipeline.
        
        Args:
            topic: Topic for content generation (optional)
            count: Number of products to select
            max_price: Maximum price filter
            csv_file: Specific CSV file to load
            **kwargs: Additional options
        
        Returns:
            Pipeline result dictionary
        """
        # Attempt to load affiliate ID
        import os
        affiliate_id = os.getenv("SHOPEE_AFFILIATE_ID", "")
        if not affiliate_id:
            env_file = project_root / ".env"
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith("SHOPEE_AFFILIATE_ID"):
                            affiliate_id = line.split("=")[1].strip().strip('"')
                            break

        # Initialize context
        context = {
            "run_id": self.run_id,
            "options": {
                "topic": topic,
                "count": count,
                "max_price": max_price,
                "csv_file": csv_file,
                "affiliate_id": affiliate_id,
                **kwargs
            },
            "step_results": {}
        }
        
        # Get steps to run based on mode
        steps_to_run = self.step_order.get(self.mode, self.step_order["full"])
        
        print_header(f"🛒 Shopee Affiliate Pipeline - {self.mode.upper()} Mode")
        print_info(f"Run ID: {self.run_id}")
        print_info(f"Steps: {' → '.join(steps_to_run)}")
        print()
        
        # Initialize state if using state manager
        if self.state:
            self.state.create_run(
                self.run_id,
                self.PIPELINE_NAME,
                {"mode": self.mode, "options": context["options"]}
            )
        
        # Execute steps
        for step_name in steps_to_run:
            step = self.steps.get(step_name)
            if not step:
                continue
            
            print_header(f"Step: {step_name}")
            
            # Start step in state manager
            if self.state:
                self.state.start_step(step_name)
            
            try:
                result = step.execute(context)
                context["step_results"][step_name] = result.to_dict()
                
                if self.state:
                    if result.success:
                        self.state.complete_step(
                            step_name,
                            output_data=result.output_data,
                            warnings=result.warnings
                        )
                    else:
                        error_msg = result.error.message if result.error else "Unknown error"
                        self.state.fail_step(step_name, error_msg)
                
                if not result.success:
                    print_error(f"Step failed: {step_name}")
                    if result.error:
                        print_error(f"Error: {result.error.message}")
                    
                    # Check if we should continue
                    if result.error and result.error.severity == ErrorSeverity.CRITICAL:
                        print_error("Critical error - stopping pipeline")
                        break
                else:
                    print_success(f"Step completed: {step_name}")
                    
            except Exception as e:
                self.logger.error(f"Step {step_name} raised exception: {e}")
                context["step_results"][step_name] = {
                    "success": False,
                    "error": str(e)
                }
                
                if self.state:
                    self.state.fail_step(step_name, str(e))
                
                print_error(f"Step exception: {step_name} - {e}")
                break
        
        # Finalize
        final_result = {
            "run_id": self.run_id,
            "pipeline": self.PIPELINE_NAME,
            "mode": self.mode,
            "success": self._check_success(context),
            "step_results": context["step_results"],
            "output_dir": str(self.output_dir)
        }
        
        # Get final output
        ready_data = context["step_results"].get("ready_to_post", {}).get("output_data", {})
        if ready_data:
            final_result["posts"] = ready_data.get("packaged_posts", [])
            final_result["output_dir"] = ready_data.get("output_dir", str(self.output_dir))
        
        if self.state:
            from common.state_manager import PipelineStatus
            status = PipelineStatus.COMPLETED if final_result["success"] else PipelineStatus.FAILED
            self.state.update_status(status)
        
        print()
        print_header("Pipeline Complete")
        if final_result["success"]:
            print_success(f"✓ Pipeline completed successfully!")
            if ready_data.get("output_dir"):
                print_info(f"Output: {ready_data['output_dir']}")
        else:
            print_error("✗ Pipeline completed with errors")
        
        return final_result
    
    def _check_success(self, context: Dict[str, Any]) -> bool:
        """Check if pipeline completed successfully"""
        step_results = context.get("step_results", {})
        
        # At minimum, load_products and select_products should succeed
        required_steps = ["load_products", "select_products"]
        
        for step in required_steps:
            if step in step_results:
                if not step_results[step].get("success", False):
                    return False
        
        return True
    
    def get_available_steps(self) -> List[str]:
        """Get list of available steps"""
        return list(self.steps.keys())
    
    def run_single_step(
        self,
        step_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> StepResult:
        """
        Run a single step.
        
        Args:
            step_name: Name of step to run
            context: Pipeline context (will create empty if not provided)
        
        Returns:
            StepResult
        """
        step = self.steps.get(step_name)
        if not step:
            return StepResult(
                success=False,
                error=ValueError(f"Unknown step: {step_name}")
            )
        
        if context is None:
            context = {"run_id": self.run_id, "step_results": {}, "options": {}}
        
        return step.execute(context)


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        description="Shopee Affiliate Pipeline - Generate affiliate content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline
  python pipeline_controller.py --mode full
  
  # Quick mode (skip images and links)
  python pipeline_controller.py --mode quick
  
  # Content only
  python pipeline_controller.py --mode content-only
  
  # Custom product count and price
  python pipeline_controller.py --count 6 --max-price 300
  
  # Specific CSV file
  python pipeline_controller.py --csv data/products.csv
  
  # Dry run
  python pipeline_controller.py --dry-run
        """
    )
    
    # Mode options
    parser.add_argument(
        "--mode", "-m",
        choices=["full", "quick", "content-only", "links-only", "resume"],
        default="full",
        help="Pipeline mode (default: full)"
    )
    
    # Product options
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=4,
        help="Number of products to select (default: 4)"
    )
    
    parser.add_argument(
        "--max-price",
        type=int,
        default=500,
        help="Maximum price filter (default: 500)"
    )
    
    parser.add_argument(
        "--csv",
        type=str,
        help="Specific CSV file to load"
    )
    
    # Content options
    parser.add_argument(
        "--topic", "-t",
        type=str,
        help="Topic for content generation"
    )
    
    # Execution options
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    
    parser.add_argument(
        "--resume",
        type=str,
        help="Resume from run ID"
    )
    
    parser.add_argument(
        "--step",
        type=str,
        help="Run single step only"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output directory"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger("affiliate_pipeline")
    
    # Handle dry run
    if args.dry_run:
        print_header("🔍 DRY RUN - No changes will be made")
        print(f"Mode: {args.mode}")
        print(f"Product count: {args.count}")
        print(f"Max price: {args.max_price}")
        if args.csv:
            print(f"CSV file: {args.csv}")
        if args.topic:
            print(f"Topic: {args.topic}")
        return 0
    
    # Initialize state manager
    state_manager = StateManager(project_root, "shopee_affiliate")
    
    # Create pipeline
    output_dir = Path(args.output) if args.output else None
    
    pipeline = AffiliatePipeline(
        mode=args.mode,
        output_dir=output_dir,
        state_manager=state_manager
    )
    
    # Handle single step
    if args.step:
        result = pipeline.run_single_step(args.step)
        print(f"\nStep result: {'Success' if result.success else 'Failed'}")
        return 0 if result.success else 1
    
    # Handle resume
    if args.resume:
        print_info(f"Resuming from run: {args.resume}")
        # Load previous state and continue
        # This would require additional implementation
        print_error("Resume functionality not yet implemented")
        return 1
    
    # Run pipeline
    result = pipeline.run(
        topic=args.topic,
        count=args.count,
        max_price=args.max_price,
        csv_file=args.csv
    )
    
    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""
Lookforward Pipeline Controller
Main controller for the content generation pipeline
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
root_dir = project_root.parent

sys.path.insert(0, str(root_dir))

from common.pipeline_base import BasePipeline, PipelineMode
from common.utils import setup_logger, print_header, print_success, print_error, print_info

# Import steps
from steps import (
    BaseLookforwardStep,
    StepStrategy,
    StepContent,
    StepImages,
    StepReadyToPost,
    StepPublishFb
)


class LookforwardPipeline(BasePipeline):
    """
    Lookforward Content Pipeline.
    
    Generates tech authority content with:
    - Strategy analysis
    - Content writing
    - Image generation (optional)
    - Ready-to-post package
    """
    
    # Define pipeline steps
    STEPS = ["strategy", "content", "images", "ready_to_post", "publish_fb"]
    
    # Mode-specific step configurations
    MODE_STEPS = {
        "full": ["strategy", "content", "images", "ready_to_post", "publish_fb"],
        "quick": ["strategy", "content", "ready_to_post", "publish_fb"],
        "strategy-only": ["strategy"],
        "content-only": ["content", "ready_to_post"],
    }
    
    def __init__(self):
        super().__init__(
            project_root=project_root,
            project_id="lookforward",
            logger=setup_logger("LookforwardPipeline")
        )
        
        # Initialize step instances
        self.step_instances = {
            "strategy": StepStrategy(),
            "content": StepContent(),
            "images": StepImages(),
            "ready_to_post": StepReadyToPost(),
            "publish_fb": StepPublishFb()
        }
    
    def run(
        self,
        topic: str,
        mode: str = "full",
        options: Dict[str, Any] = None,
        resume_from: str = None
    ) -> Dict[str, Any]:
        """
        Run the pipeline.
        
        Args:
            topic: Content topic
            mode: Pipeline mode (full, quick, strategy-only, content-only)
            options: Additional options
                - gen_images: bool - Enable image generation
                - dry_run: bool - Preview without executing
            resume_from: Step name to resume from
        
        Returns:
            Dict with run results
        """
        options = options or {}
        
        # Handle dry run
        if options.get("dry_run"):
            return self._dry_run(topic, options)
        
        # Run pipeline
        result = super().run(topic, mode, options, resume_from)
        
        # Print summary
        if result.get("success"):
            print_header("✅ WORKFLOW COMPLETE!")
            progress = result.get("progress", {})
            print_success(f"Run ID: {progress.get('run_id')}")
            print_success(f"Completed steps: {progress.get('completed_steps')}/{progress.get('total_steps')}")
        else:
            print_error(f"Pipeline failed: {result.get('error')}")
        
        return result


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Lookforward Content Pipeline - Generate tech authority content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline with images
  python pipeline_controller.py "AI Trends 2026" --gen-images
  
  # Quick mode (no images)
  python pipeline_controller.py "DeepSeek R1 Analysis" --mode quick
  
  # Strategy only
  python pipeline_controller.py "Quantum Computing" --mode strategy-only
  
  # Resume from failed step
  python pipeline_controller.py --resume-from content
  
  # Dry run (preview)
  python pipeline_controller.py "AI Agents" --dry-run
        """
    )
    
    parser.add_argument(
        "topic",
        nargs="?",
        help="Topic to generate content for"
    )
    
    parser.add_argument(
        "--mode",
        choices=["full", "quick", "strategy-only", "content-only"],
        default="full",
        help="Pipeline mode (default: full)"
    )
    
    parser.add_argument(
        "--gen-images",
        action="store_true",
        help="Enable image generation (default: disabled)"
    )
    
    parser.add_argument(
        "--resume-from",
        metavar="STEP",
        help="Resume from a specific step (strategy, content, images, ready_to_post)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview pipeline without executing"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current pipeline status"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show pipeline run history"
    )
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = LookforwardPipeline()
    
    # Handle status command
    if args.status:
        progress = pipeline.get_progress()
        print_header("Pipeline Status")
        print(f"  Run ID: {progress.get('run_id', 'None')}")
        print(f"  Status: {progress.get('status', 'idle')}")
        print(f"  Current Step: {progress.get('current_step', 'None')}")
        print(f"  Progress: {progress.get('progress_percent', 0)}%")
        return
    
    # Handle history command
    if args.history:
        history = pipeline.get_history(limit=5)
        print_header("Pipeline History")
        for run in history:
            print(f"  {run.get('run_id')}: {run.get('status')} - {run.get('topic', 'N/A')}")
        return
    
    # Handle resume
    if args.resume_from:
        if args.resume_from not in LookforwardPipeline.STEPS:
            print_error(f"Invalid step: {args.resume_from}")
            print_info(f"Valid steps: {LookforwardPipeline.STEPS}")
            return
        
        result = pipeline.run(
            topic="",  # Will be loaded from state
            mode="resume",
            resume_from=args.resume_from
        )
        return
    
    # Require topic for normal run
    if not args.topic:
        parser.print_help()
        return
    
    # Build options
    options = {
        "gen_images": args.gen_images,
        "dry_run": args.dry_run
    }
    
    # Run pipeline
    result = pipeline.run(
        topic=args.topic,
        mode=args.mode,
        options=options
    )
    
    # Exit with appropriate code
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()

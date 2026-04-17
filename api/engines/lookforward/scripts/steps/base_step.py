"""
Base Step for Lookforward Pipeline
Provides common functionality for all lookforward steps
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Add project root to path
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
root_dir = project_root.parent  # MultiContentApp root

sys.path.insert(0, str(root_dir))

from common.pipeline_base import BaseStep, StepResult
from common.error_handler import PipelineError, AIError, ErrorSeverity
from common.utils import setup_logger
from common.ai_client import create_ai_client


class BaseLookforwardStep(BaseStep):
    """
    Base class for Lookforward pipeline steps.
    
    Provides:
    - AI client initialization
    - Common configuration
    - Utility methods
    """
    
    def __init__(self, name: str = None):
        super().__init__(name)
        self.project_root = project_root
        self.root_dir = root_dir
        self.data_dir = self.root_dir / "data"
        # New organized directory structure
        self.drafts_dir = self.data_dir / "output" / "lookforward" / "drafts"
        self.ready_dir = self.data_dir / "output" / "lookforward" / "ready_to_post"
        self.published_dir = self.data_dir / "output" / "lookforward" / "published"
        self.state_dir = self.data_dir / "state" / "lookforward"
        
        # Ensure directories exist
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.ready_dir.mkdir(parents=True, exist_ok=True)
        self.published_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)
    
    def get_ai_client(self, logger: logging.Logger = None):
        """
        Get AI client instance.
        
        Args:
            logger: Logger instance
        
        Returns:
            AI client or None
        """
        return create_ai_client(logger or self.logger)
    
    def get_output_dir(self, context: Dict[str, Any]) -> Path:
        """
        Get output directory for current run.
        
        Args:
            context: Pipeline context
        
        Returns:
            Path to output directory
        """
        from common.utils import get_date_str, sanitize_filename
        from datetime import datetime
        
        date_str = get_date_str()
        topic = context.get("topic", "untitled")
        safe_topic = sanitize_filename(topic, max_length=50)
        timestamp = datetime.now().strftime("%H%M%S")
        
        output_dir = self.drafts_dir / date_str / f"{safe_topic}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir
    
    def handle_ai_error(self, error: Exception, step_name: str) -> StepResult:
        """
        Handle AI-related errors.
        
        Args:
            error: The exception
            step_name: Name of the step
        
        Returns:
            StepResult with error
        """
        if isinstance(error, PipelineError):
            return StepResult(success=False, error=error)
        
        # Wrap unknown errors
        ai_error = AIError(
            str(error),
            step_name=step_name,
            severity=ErrorSeverity.MEDIUM,
            recoverable=True
        )
        return StepResult(success=False, error=ai_error)

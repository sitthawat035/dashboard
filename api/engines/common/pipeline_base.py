"""
Pipeline Base Module
Provides base classes for building modular pipelines
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from enum import Enum
import logging

from .state_manager import StateManager, PipelineStatus, StepStatus
from .error_handler import (
    ErrorHandler, PipelineError, RetryStrategy,
    ErrorSeverity, ErrorCategory
)


class StepResult:
    """Result of a step execution"""
    
    def __init__(
        self,
        success: bool,
        output_file: str = None,
        output_data: Dict = None,
        warnings: List[str] = None,
        error: PipelineError = None
    ):
        self.success = success
        self.output_file = output_file
        self.output_data = output_data or {}
        self.warnings = warnings or []
        self.error = error
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "output_file": self.output_file,
            "output_data": self.output_data,
            "warnings": self.warnings,
            "error": self.error.to_dict() if self.error else None
        }


class BaseStep(ABC):
    """
    Abstract base class for pipeline steps.
    
    All steps must inherit from this class and implement execute().
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"Step.{self.name}")
    
    @abstractmethod
    def execute(
        self,
        context: Dict[str, Any],
        **kwargs
    ) -> StepResult:
        """
        Execute the step.
        
        Args:
            context: Pipeline context with shared data
            **kwargs: Additional step-specific arguments
        
        Returns:
            StepResult with execution outcome
        """
        pass
    
    def validate_inputs(
        self,
        context: Dict[str, Any],
        required_keys: List[str] = None
    ) -> Optional[PipelineError]:
        """
        Validate that required inputs are present in context.
        
        Args:
            context: Pipeline context
            required_keys: List of required keys
        
        Returns:
            PipelineError if validation fails, None otherwise
        """
        if not required_keys:
            return None
        
        missing = [k for k in required_keys if k not in context]
        if missing:
            return PipelineError(
                f"Missing required inputs: {missing}",
                code="STEP_DEPENDENCY",
                severity=ErrorSeverity.HIGH,
                step_name=self.name,
                details={"missing_keys": missing}
            )
        return None
    
    def get_previous_output(
        self,
        context: Dict[str, Any],
        step_name: str
    ) -> Optional[Dict]:
        """
        Get output from a previous step.
        
        Args:
            context: Pipeline context
            step_name: Name of the previous step
        
        Returns:
            Output data from the step, or None
        """
        step_results = context.get("step_results", {})
        step = step_results.get(step_name, {})
        return step.get("output_data")


class PipelineMode(Enum):
    """Pipeline execution modes"""
    FULL = "full"                    # Run all steps
    QUICK = "quick"                  # Skip optional steps
    SINGLE_STEP = "single_step"      # Run only one step
    RESUME = "resume"                # Resume from failed step
    DRY_RUN = "dry_run"              # Preview without executing


class BasePipeline(ABC):
    """
    Abstract base class for pipelines.
    
    Provides:
    - Step orchestration
    - State management
    - Error handling
    - Progress tracking
    """
    
    # Subclasses should define their steps
    STEPS: List[str] = []
    
    # Mode-specific step configurations
    MODE_STEPS: Dict[str, List[str]] = {
        "full": None,      # None means use STEPS
        "quick": None,     # Override in subclass
    }
    
    def __init__(
        self,
        project_root: Path,
        project_id: str,
        logger: logging.Logger = None
    ):
        self.project_root = Path(project_root)
        self.project_id = project_id
        self.logger = logger or logging.getLogger(f"Pipeline.{project_id}")
        
        # Initialize state manager
        self.state = StateManager(
            project_root,
            project_id,
            self.logger
        )
        
        # Initialize error handler
        self.error_handler = ErrorHandler(
            project_root,
            self.logger
        )
        
        # Initialize retry strategy
        self.retry_strategy = RetryStrategy(
            max_retries=3,
            base_delay=5.0,
            exponential_backoff=True
        )
        
        # Step instances (populated in subclass)
        self.step_instances: Dict[str, BaseStep] = {}
        
        # Register default recovery strategies
        self._register_recovery_strategies()
    
    def _register_recovery_strategies(self):
        """Register default recovery strategies"""
        
        def recover_rate_limit(error):
            import time
            time.sleep(60)
            return {"action": "retry"}
        
        def recover_timeout(error):
            return {"action": "retry", "timeout_multiplier": 1.5}
        
        self.error_handler.register_recovery_strategy(
            "AI_RATE_LIMIT", recover_rate_limit
        )
        self.error_handler.register_recovery_strategy(
            "AI_TIMEOUT", recover_timeout
        )
        self.error_handler.register_recovery_strategy(
            "NETWORK_TIMEOUT", recover_timeout
        )
    
    def get_steps_for_mode(self, mode: str) -> List[str]:
        """
        Get list of steps to run based on mode.
        
        Args:
            mode: Pipeline mode
        
        Returns:
            List of step names
        """
        if mode in self.MODE_STEPS and self.MODE_STEPS[mode] is not None:
            return self.MODE_STEPS[mode]
        return self.STEPS
    
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
            topic: Topic/title for this run
            mode: Pipeline mode (full, quick, single_step, resume, dry_run)
            options: Additional options
            resume_from: Step name to resume from (for resume mode)
        
        Returns:
            Dict with run results
        """
        options = options or {}
        
        # Handle dry run
        if mode == "dry_run":
            return self._dry_run(topic, options)
        
        # Determine steps to run
        if mode == "resume" or resume_from:
            return self._resume_run(topic, options, resume_from)
        
        if mode == "single_step":
            step_name = options.get("step_name")
            if not step_name:
                return {
                    "success": False,
                    "error": "step_name required for single_step mode"
                }
            return self._run_single_step(topic, step_name, options)
        
        # Normal run
        return self._run_normal(topic, mode, options)
    
    def _run_normal(
        self,
        topic: str,
        mode: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a normal pipeline run"""
        steps = self.get_steps_for_mode(mode)
        
        # Create run
        run_id = self.state.create_run(topic, {
            "mode": mode,
            **options
        }, steps)
        
        self.logger.info(f"Starting pipeline run: {run_id} (mode: {mode})")
        
        # Initialize context
        context = {
            "topic": topic,
            "options": options,
            "run_id": run_id,
            "step_results": {}
        }
        
        try:
            # Execute steps
            for step_name in steps:
                result = self._execute_step(step_name, context, options)
                
                if not result.success:
                    return {
                        "success": False,
                        "run_id": run_id,
                        "error": result.error.to_dict() if result.error else None,
                        "progress": self.state.get_progress()
                    }
            
            # All steps completed
            self.state.update_status(PipelineStatus.COMPLETED)
            archive_path = self.state.archive_run()
            
            return {
                "success": True,
                "run_id": run_id,
                "archive_path": archive_path,
                "progress": self.state.get_progress()
            }
        
        except Exception as e:
            self.logger.exception("Pipeline failed with unexpected error")
            return {
                "success": False,
                "run_id": run_id,
                "error": str(e),
                "progress": self.state.get_progress()
            }
    
    def _execute_step(
        self,
        step_name: str,
        context: Dict[str, Any],
        options: Dict[str, Any]
    ) -> StepResult:
        """
        Execute a single step with error handling.
        
        Args:
            step_name: Name of the step
            context: Pipeline context
            options: Pipeline options
        
        Returns:
            StepResult
        """
        self.state.start_step(step_name)
        
        # Get step instance
        step = self.step_instances.get(step_name)
        if not step:
            error = PipelineError(
                f"Step not found: {step_name}",
                code="STEP_NOT_FOUND",
                severity=ErrorSeverity.HIGH,
                step_name=step_name,
                recoverable=False
            )
            self.state.fail_step(step_name, error.message, error.to_dict())
            return StepResult(success=False, error=error)
        
        try:
            # Execute with retry
            result = self.retry_strategy.execute_with_retry(
                step.execute,
                context,
                on_retry=lambda attempt, err: self.logger.warning(
                    f"Retry {attempt} for {step_name}: {err}"
                )
            )
            
            # Update state
            if result.success:
                self.state.complete_step(
                    step_name,
                    output_file=result.output_file,
                    output_data=result.output_data,
                    warnings=result.warnings
                )
                
                # Update context
                context["step_results"][step_name] = {
                    "status": "completed",
                    "output_data": result.output_data,
                    "output_file": result.output_file
                }
            else:
                self.state.fail_step(
                    step_name,
                    result.error.message if result.error else "Unknown error",
                    result.error.to_dict() if result.error else None
                )
            
            return result
        
        except PipelineError as e:
            # Handle known pipeline errors
            action = self.error_handler.handle_error(e, self.state, step_name)
            
            return StepResult(
                success=False,
                error=e if e else PipelineError(
                    "Unknown error",
                    code="UNKNOWN_ERROR",
                    step_name=step_name
                )
            )
        
        except Exception as e:
            # Handle unexpected errors
            error = PipelineError(
                str(e),
                code="UNEXPECTED_ERROR",
                severity=ErrorSeverity.HIGH,
                step_name=step_name
            )
            self.error_handler.handle_error(error, self.state, step_name)
            
            return StepResult(success=False, error=error)
    
    def _resume_run(
        self,
        topic: str,
        options: Dict[str, Any],
        resume_from: str = None
    ) -> Dict[str, Any]:
        """Resume a failed or paused pipeline run"""
        # Load current state
        state = self.state.load_state()
        
        if not state:
            return {
                "success": False,
                "error": "No run to resume"
            }
        
        # Find failed step if not specified
        if not resume_from:
            progress = self.state.get_progress()
            resume_from = progress.get("resume_from")
        
        if not resume_from:
            return {
                "success": False,
                "error": "No failed step to resume from"
            }
        
        self.logger.info(f"Resuming from step: {resume_from}")
        
        # Rebuild context from state
        context = {
            "topic": state.get("topic"),
            "options": state.get("options", {}),
            "run_id": state["run_id"],
            "step_results": state["step_results"]
        }
        
        # Get remaining steps
        steps = state["metadata"].get("steps", [])
        try:
            step_index = steps.index(resume_from)
        except ValueError:
            return {
                "success": False,
                "error": f"Step not found: {resume_from}"
            }
        
        remaining_steps = steps[step_index:]
        
        # Update status
        self.state.update_status(PipelineStatus.RUNNING)
        
        # Execute remaining steps
        for step_name in remaining_steps:
            result = self._execute_step(step_name, context, options)
            
            if not result.success:
                return {
                    "success": False,
                    "run_id": state["run_id"],
                    "error": result.error.to_dict() if result.error else None,
                    "progress": self.state.get_progress()
                }
        
        # All steps completed
        self.state.update_status(PipelineStatus.COMPLETED)
        archive_path = self.state.archive_run()
        
        return {
            "success": True,
            "run_id": state["run_id"],
            "archive_path": archive_path,
            "progress": self.state.get_progress()
        }
    
    def _run_single_step(
        self,
        topic: str,
        step_name: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run a single step"""
        # Create minimal run
        run_id = self.state.create_run(topic, {
            "mode": "single_step",
            "step_name": step_name,
            **options
        }, [step_name])
        
        context = {
            "topic": topic,
            "options": options,
            "run_id": run_id,
            "step_results": {}
        }
        
        result = self._execute_step(step_name, context, options)
        
        if result.success:
            self.state.update_status(PipelineStatus.COMPLETED)
        else:
            self.state.update_status(PipelineStatus.FAILED)
        
        self.state.archive_run()
        
        return {
            "success": result.success,
            "run_id": run_id,
            "result": result.to_dict()
        }
    
    def _dry_run(
        self,
        topic: str,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Preview pipeline without executing"""
        mode = options.get("mode", "full")
        steps = self.get_steps_for_mode(mode)
        
        return {
            "success": True,
            "dry_run": True,
            "topic": topic,
            "mode": mode,
            "steps": steps,
            "options": options,
            "message": "Dry run completed - no changes made"
        }
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current pipeline progress"""
        return self.state.get_progress()
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get historical runs"""
        return self.state.get_history(limit)
    
    def cancel(self) -> Dict[str, Any]:
        """Cancel current run"""
        state = self.state.load_state()
        if not state:
            return {"success": False, "error": "No active run to cancel"}
        
        self.state.update_status(PipelineStatus.CANCELLED)
        self.state.archive_run()
        
        return {
            "success": True,
            "run_id": state["run_id"],
            "message": "Pipeline cancelled"
        }
    
    def get_step_output(self, step_name: str) -> Optional[Dict]:
        """Get output from a specific step"""
        return self.state.get_step_output(step_name)
    
    def is_step_completed(self, step_name: str) -> bool:
        """Check if a step is completed"""
        return self.state.is_step_completed(step_name)


# ============================================
# Utility Functions
# ============================================

def create_step_decorator(
    step_name: str,
    required_inputs: List[str] = None
):
    """
    Decorator to mark a function as a pipeline step.
    
    Usage:
        @create_step_decorator("my_step", required_inputs=["previous_step"])
        def my_step_function(context, **kwargs):
            # Step logic
            return StepResult(success=True, output_data={...})
    """
    def decorator(func):
        func._is_step = True
        func._step_name = step_name
        func._required_inputs = required_inputs or []
        return func
    return decorator
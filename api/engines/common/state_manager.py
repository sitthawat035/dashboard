"""
Pipeline State Management Module
Manages state persistence and retrieval for pipeline runs
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from enum import Enum
import logging


class PipelineStatus(Enum):
    """Pipeline execution status"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StateManager:
    """
    Manages pipeline state persistence and retrieval.
    
    Features:
    - Persistent state storage in JSON files
    - Run history with archiving
    - Step-by-step progress tracking
    - Resume capability from any failed step
    """
    
    def __init__(
        self, 
        project_root: Path, 
        project_id: str,
        logger: logging.Logger = None
    ):
        """
        Initialize StateManager.
        
        Args:
            project_root: Root directory of the project
            project_id: Unique identifier for the project (e.g., "lookforward", "shopee")
            logger: Optional logger instance
        """
        self.project_root = Path(project_root)
        self.project_id = project_id
        self.logger = logger or logging.getLogger(__name__)
        
        # Setup directories
        self.agent_dir = self.project_root / ".agent"
        self.state_file = self.agent_dir / "pipeline_state.json"
        self.history_dir = self.agent_dir / "pipeline_history"
        
        # Ensure directories exist
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def create_run(
        self, 
        topic: str, 
        options: Dict[str, Any],
        steps: List[str] = None
    ) -> str:
        """
        Create a new pipeline run and return run_id.
        
        Args:
            topic: Topic or title for this run
            options: Pipeline options/configuration
            steps: List of step names (optional)
        
        Returns:
            run_id: Unique identifier for this run
        """
        # Generate run ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        run_id = f"{self.project_id[:2]}_{timestamp}"
        
        # Create initial state
        state = {
            "run_id": run_id,
            "project_id": self.project_id,
            "topic": topic,
            "status": PipelineStatus.IDLE.value,
            "current_step": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "options": options,
            "step_results": {},
            "metadata": {
                "total_steps": len(steps) if steps else 0,
                "completed_steps": 0,
                "failed_steps": 0,
                "skipped_steps": 0,
                "estimated_remaining_seconds": None,
                "steps": steps or []
            }
        }
        
        # Initialize step results
        if steps:
            for step in steps:
                state["step_results"][step] = {
                    "step_name": step,
                    "status": StepStatus.PENDING.value,
                    "started_at": None,
                    "completed_at": None,
                    "duration_seconds": None,
                    "output_file": None,
                    "output_data": None,
                    "errors": [],
                    "warnings": []
                }
        
        self._save_state(state)
        self.logger.info(f"Created pipeline run: {run_id}")
        
        return run_id
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load current pipeline state.
        
        Returns:
            State dict or None if no active state
        """
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Failed to load state: {e}")
            return None
    
    def _save_state(self, state: Dict[str, Any]):
        """
        Save state to file.
        
        Args:
            state: State dictionary to save
        """
        state["updated_at"] = datetime.now().isoformat()
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except IOError as e:
            self.logger.error(f"Failed to save state: {e}")
            raise
    
    def update_status(self, status: PipelineStatus):
        """
        Update pipeline status.
        
        Args:
            status: New status
        """
        state = self.load_state()
        if state:
            state["status"] = status.value
            self._save_state(state)
            self.logger.info(f"Pipeline status updated: {status.value}")
    
    def start_step(
        self, 
        step_name: str, 
        total_steps: int = None
    ):
        """
        Mark a step as started.
        
        Args:
            step_name: Name of the step
            total_steps: Total number of steps (optional, for progress calculation)
        """
        state = self.load_state()
        if not state:
            self.logger.warning("No state to update")
            return
        
        state["current_step"] = step_name
        state["status"] = PipelineStatus.RUNNING.value
        
        if total_steps:
            state["metadata"]["total_steps"] = total_steps
        
        # Initialize or update step result
        if step_name not in state["step_results"]:
            state["step_results"][step_name] = {
                "step_name": step_name,
                "status": StepStatus.PENDING.value,
                "started_at": None,
                "completed_at": None,
                "duration_seconds": None,
                "output_file": None,
                "output_data": None,
                "errors": [],
                "warnings": []
            }
        
        state["step_results"][step_name]["status"] = StepStatus.RUNNING.value
        state["step_results"][step_name]["started_at"] = datetime.now().isoformat()
        
        self._save_state(state)
        self.logger.info(f"Step started: {step_name}")
    
    def complete_step(
        self, 
        step_name: str, 
        output_file: str = None,
        output_data: Dict = None,
        warnings: List[str] = None
    ):
        """
        Mark a step as completed.
        
        Args:
            step_name: Name of the step
            output_file: Path to output file (optional)
            output_data: Additional output data (optional)
            warnings: List of warning messages (optional)
        """
        state = self.load_state()
        if not state:
            self.logger.warning("No state to update")
            return
        
        step = state["step_results"].get(step_name, {})
        step["status"] = StepStatus.COMPLETED.value
        step["completed_at"] = datetime.now().isoformat()
        
        # Calculate duration
        if step.get("started_at"):
            try:
                start = datetime.fromisoformat(step["started_at"])
                end = datetime.fromisoformat(step["completed_at"])
                step["duration_seconds"] = int((end - start).total_seconds())
            except (ValueError, TypeError):
                pass
        
        step["output_file"] = output_file
        step["output_data"] = output_data
        if warnings:
            step["warnings"] = warnings
        
        state["step_results"][step_name] = step
        
        # Update metadata
        state["metadata"]["completed_steps"] = sum(
            1 for s in state["step_results"].values() 
            if s.get("status") == StepStatus.COMPLETED.value
        )
        
        self._save_state(state)
        self.logger.info(f"Step completed: {step_name}")
    
    def fail_step(
        self, 
        step_name: str, 
        error: str, 
        error_details: Dict = None
    ):
        """
        Mark a step as failed.
        
        Args:
            step_name: Name of the step
            error: Error message
            error_details: Additional error details (optional)
        """
        state = self.load_state()
        if not state:
            self.logger.warning("No state to update")
            return
        
        step = state["step_results"].get(step_name, {})
        step["status"] = StepStatus.FAILED.value
        step["completed_at"] = datetime.now().isoformat()
        
        # Calculate duration
        if step.get("started_at"):
            try:
                start = datetime.fromisoformat(step["started_at"])
                end = datetime.fromisoformat(step["completed_at"])
                step["duration_seconds"] = int((end - start).total_seconds())
            except (ValueError, TypeError):
                pass
        
        step["errors"].append({
            "message": error,
            "details": error_details,
            "timestamp": datetime.now().isoformat()
        })
        
        state["step_results"][step_name] = step
        state["status"] = PipelineStatus.FAILED.value
        
        # Update metadata
        state["metadata"]["failed_steps"] = sum(
            1 for s in state["step_results"].values() 
            if s.get("status") == StepStatus.FAILED.value
        )
        
        self._save_state(state)
        self.logger.error(f"Step failed: {step_name} - {error}")
    
    def skip_step(
        self, 
        step_name: str, 
        reason: str = None
    ):
        """
        Mark a step as skipped.
        
        Args:
            step_name: Name of the step
            reason: Reason for skipping (optional)
        """
        state = self.load_state()
        if not state:
            self.logger.warning("No state to update")
            return
        
        step = state["step_results"].get(step_name, {})
        step["status"] = StepStatus.SKIPPED.value
        step["completed_at"] = datetime.now().isoformat()
        
        if reason:
            step["warnings"].append({
                "message": f"Skipped: {reason}",
                "timestamp": datetime.now().isoformat()
            })
        
        state["step_results"][step_name] = step
        
        # Update metadata
        state["metadata"]["skipped_steps"] = sum(
            1 for s in state["step_results"].values() 
            if s.get("status") == StepStatus.SKIPPED.value
        )
        
        self._save_state(state)
        self.logger.info(f"Step skipped: {step_name} - {reason}")
    
    def get_progress(self) -> Dict[str, Any]:
        """
        Get current progress information.
        
        Returns:
            Dict with progress details
        """
        state = self.load_state()
        if not state:
            return {"error": "No active pipeline run"}
        
        total = state["metadata"].get("total_steps", 0)
        completed = state["metadata"].get("completed_steps", 0)
        failed = state["metadata"].get("failed_steps", 0)
        skipped = state["metadata"].get("skipped_steps", 0)
        
        progress_percent = (completed / total * 100) if total > 0 else 0
        
        # Calculate total duration
        total_duration = sum(
            s.get("duration_seconds", 0) or 0 
            for s in state["step_results"].values()
        )
        
        return {
            "run_id": state["run_id"],
            "topic": state.get("topic"),
            "status": state["status"],
            "current_step": state.get("current_step"),
            "progress_percent": round(progress_percent, 1),
            "completed_steps": completed,
            "total_steps": total,
            "failed_steps": failed,
            "skipped_steps": skipped,
            "total_duration_seconds": total_duration,
            "step_results": state["step_results"],
            "can_resume": state["status"] == PipelineStatus.FAILED.value,
            "resume_from": self._get_resume_step(state),
            "created_at": state.get("created_at"),
            "updated_at": state.get("updated_at")
        }
    
    def _get_resume_step(self, state: Dict) -> Optional[str]:
        """
        Determine which step to resume from.
        
        Args:
            state: Current state
        
        Returns:
            Step name to resume from, or None
        """
        if state["status"] != PipelineStatus.FAILED.value:
            return None
        
        # Find the first failed step
        steps = state["metadata"].get("steps", [])
        for step_name in steps:
            step = state["step_results"].get(step_name, {})
            if step.get("status") == StepStatus.FAILED.value:
                return step_name
        
        return None
    
    def archive_run(self) -> Optional[str]:
        """
        Archive current run to history.
        
        Returns:
            Path to archived file, or None
        """
        state = self.load_state()
        if not state:
            return None
        
        # Save to history
        history_file = self.history_dir / f"{state['run_id']}.json"
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            # Clear current state
            self.state_file.unlink(missing_ok=True)
            
            self.logger.info(f"Archived run: {state['run_id']}")
            return str(history_file)
        except IOError as e:
            self.logger.error(f"Failed to archive run: {e}")
            return None
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        Get historical runs.
        
        Args:
            limit: Maximum number of runs to return
        
        Returns:
            List of historical run states
        """
        if not self.history_dir.exists():
            return []
        
        history_files = sorted(
            self.history_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]
        
        history = []
        for f in history_files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    history.append(json.load(file))
            except (json.JSONDecodeError, IOError) as e:
                self.logger.warning(f"Failed to load history file {f}: {e}")
        
        return history
    
    def get_run_by_id(self, run_id: str) -> Optional[Dict]:
        """
        Get a specific run by ID.
        
        Args:
            run_id: Run identifier
        
        Returns:
            Run state or None
        """
        # Check current state first
        state = self.load_state()
        if state and state.get("run_id") == run_id:
            return state
        
        # Check history
        history_file = self.history_dir / f"{run_id}.json"
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Failed to load run {run_id}: {e}")
        
        return None
    
    def clear_state(self):
        """Clear current state file."""
        self.state_file.unlink(missing_ok=True)
        self.logger.info("State cleared")
    
    def get_step_output(self, step_name: str) -> Optional[Dict]:
        """
        Get output data from a specific step.
        
        Args:
            step_name: Name of the step
        
        Returns:
            Step output data or None
        """
        state = self.load_state()
        if not state:
            return None
        
        step = state["step_results"].get(step_name, {})
        return step.get("output_data")
    
    def is_step_completed(self, step_name: str) -> bool:
        """
        Check if a step is completed.
        
        Args:
            step_name: Name of the step
        
        Returns:
            True if completed, False otherwise
        """
        state = self.load_state()
        if not state:
            return False
        
        step = state["step_results"].get(step_name, {})
        return step.get("status") == StepStatus.COMPLETED.value
    
    def get_completed_steps(self) -> List[str]:
        """
        Get list of completed step names.
        
        Returns:
            List of completed step names
        """
        state = self.load_state()
        if not state:
            return []
        
        return [
            name for name, step in state["step_results"].items()
            if step.get("status") == StepStatus.COMPLETED.value
        ]

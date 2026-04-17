"""
Pipeline Error Handling Module
Provides error types, handling, and recovery mechanisms
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Type, Tuple
from enum import Enum
import logging
import time
import functools


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Warning, can continue
    MEDIUM = "medium"     # Step failed, can retry
    HIGH = "high"         # Pipeline failed, needs intervention
    CRITICAL = "critical" # System error, stop everything


class ErrorCategory(Enum):
    """Error categories"""
    VALIDATION = "validation"
    AI_PROVIDER = "ai_provider"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    CONFIGURATION = "configuration"
    STATE = "state"
    UNKNOWN = "unknown"


class PipelineError(Exception):
    """
    Base error class for pipeline errors.
    
    Features:
    - Structured error information
    - Severity and category classification
    - Recovery tracking
    """
    
    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        step_name: str = None,
        details: Dict = None,
        recoverable: bool = True,
        retry_count: int = 0,
        max_retries: int = 3
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.category = category
        self.severity = severity
        self.step_name = step_name
        self.details = details or {}
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.timestamp = datetime.now().isoformat()
    
    def can_retry(self) -> bool:
        """Check if error can be retried"""
        return self.recoverable and self.retry_count < self.max_retries
    
    def increment_retry(self) -> 'PipelineError':
        """Create a new error with incremented retry count"""
        return PipelineError(
            message=self.message,
            code=self.code,
            category=self.category,
            severity=self.severity,
            step_name=self.step_name,
            details=self.details,
            recoverable=self.recoverable,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries
        )
    
    def to_dict(self) -> Dict:
        """Convert error to dictionary"""
        return {
            "error_type": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "step_name": self.step_name,
            "details": self.details,
            "recoverable": self.recoverable,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timestamp": self.timestamp
        }
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class AIError(PipelineError):
    """Error from AI provider"""
    
    def __init__(
        self,
        message: str,
        provider: str = None,
        model: str = None,
        http_status: int = None,
        api_error: str = None,
        **kwargs
    ):
        details = {
            "provider": provider,
            "model": model,
            "http_status": http_status,
            "api_error": api_error
        }
        kwargs.setdefault("category", ErrorCategory.AI_PROVIDER)
        kwargs.setdefault("code", "AI_ERROR")
        super().__init__(message, details=details, **kwargs)


class NetworkError(PipelineError):
    """Network-related error"""
    
    def __init__(
        self,
        message: str,
        url: str = None,
        timeout_seconds: int = None,
        **kwargs
    ):
        details = {
            "url": url,
            "timeout_seconds": timeout_seconds
        }
        kwargs.setdefault("category", ErrorCategory.NETWORK)
        kwargs.setdefault("code", "NETWORK_ERROR")
        super().__init__(message, details=details, **kwargs)


class ValidationError(PipelineError):
    """Validation error"""
    
    def __init__(
        self,
        message: str,
        field: str = None,
        expected: str = None,
        actual: str = None,
        **kwargs
    ):
        details = {
            "field": field,
            "expected": expected,
            "actual": actual
        }
        kwargs.setdefault("category", ErrorCategory.VALIDATION)
        kwargs.setdefault("code", "VALIDATION_ERROR")
        kwargs.setdefault("recoverable", False)
        super().__init__(message, details=details, **kwargs)


class FileError(PipelineError):
    """File system error"""
    
    def __init__(
        self,
        message: str,
        file_path: str = None,
        operation: str = None,
        **kwargs
    ):
        details = {
            "file_path": file_path,
            "operation": operation
        }
        kwargs.setdefault("category", ErrorCategory.FILE_SYSTEM)
        kwargs.setdefault("code", "FILE_ERROR")
        super().__init__(message, details=details, **kwargs)


class StateError(PipelineError):
    """State management error"""
    
    def __init__(
        self,
        message: str,
        run_id: str = None,
        step_name: str = None,
        **kwargs
    ):
        details = {
            "run_id": run_id,
            "step_name": step_name
        }
        kwargs.setdefault("category", ErrorCategory.STATE)
        kwargs.setdefault("code", "STATE_ERROR")
        super().__init__(message, details=details, **kwargs)


class ErrorHandler:
    """
    Centralized error handling for pipelines.
    
    Features:
    - Error logging to file
    - Recovery strategy registration
    - Error history tracking
    """
    
    def __init__(
        self,
        project_root: Path,
        logger: logging.Logger = None
    ):
        self.project_root = Path(project_root)
        self.log_dir = self.project_root / ".agent" / "error_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or logging.getLogger(__name__)
        
        # Error log file
        self.error_log = self.log_dir / "errors.jsonl"
        
        # Recovery strategies
        self.recovery_strategies: Dict[str, Callable] = {}
    
    def register_recovery_strategy(
        self, 
        error_code: str, 
        strategy: Callable[[PipelineError], Dict]
    ):
        """
        Register a recovery strategy for an error code.
        
        Args:
            error_code: Error code to handle
            strategy: Function that takes PipelineError and returns recovery result
        """
        self.recovery_strategies[error_code] = strategy
        self.logger.debug(f"Registered recovery strategy for: {error_code}")
    
    def handle_error(
        self,
        error: PipelineError,
        state_manager = None,
        step_name: str = None
    ) -> Dict[str, Any]:
        """
        Handle an error and return action recommendation.
        
        Args:
            error: The pipeline error
            state_manager: Optional StateManager to update
            step_name: Optional step name
        
        Returns:
            Dict with action recommendation
        """
        # Log the error
        self._log_error(error)
        
        # Update state if available
        if state_manager and step_name:
            state_manager.fail_step(
                step_name,
                error.message,
                error.to_dict()
            )
        
        # Determine action
        action = self._determine_action(error)
        
        # Try recovery if possible
        if action["action"] == "retry" and error.can_retry():
            recovery_result = self._attempt_recovery(error)
            if recovery_result["success"]:
                action["action"] = "recovered"
                action["recovery"] = recovery_result
        
        return action
    
    def _log_error(self, error: PipelineError):
        """Log error to file and logger"""
        error_data = error.to_dict()
        
        # Log to file (JSONL format for easy parsing)
        try:
            with open(self.error_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_data, ensure_ascii=False) + "\n")
        except IOError as e:
            self.logger.error(f"Failed to write error log: {e}")
        
        # Log to logger
        log_msg = f"[{error.code}] {error.message}"
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_msg)
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(log_msg)
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
    
    def _determine_action(self, error: PipelineError) -> Dict[str, Any]:
        """Determine what action to take for an error"""
        
        if error.severity == ErrorSeverity.CRITICAL:
            return {
                "action": "abort",
                "reason": "Critical error - immediate stop required",
                "error": error.to_dict()
            }
        
        if error.severity == ErrorSeverity.HIGH:
            if error.can_retry():
                return {
                    "action": "retry",
                    "reason": "High severity but recoverable",
                    "max_retries": error.max_retries,
                    "current_retry": error.retry_count,
                    "error": error.to_dict()
                }
            return {
                "action": "abort",
                "reason": "High severity and not recoverable",
                "error": error.to_dict()
            }
        
        if error.severity == ErrorSeverity.MEDIUM:
            if error.can_retry():
                return {
                    "action": "retry",
                    "reason": "Medium severity - retry recommended",
                    "max_retries": error.max_retries,
                    "current_retry": error.retry_count,
                    "error": error.to_dict()
                }
            return {
                "action": "skip",
                "reason": "Medium severity - skip step and continue",
                "error": error.to_dict()
            }
        
        # Low severity
        return {
            "action": "continue",
            "reason": "Low severity - log and continue",
            "error": error.to_dict()
        }
    
    def _attempt_recovery(self, error: PipelineError) -> Dict[str, Any]:
        """Attempt to recover from error using registered strategies"""
        strategy = self.recovery_strategies.get(error.code)
        
        if not strategy:
            return {
                "success": False,
                "reason": f"No recovery strategy for {error.code}"
            }
        
        try:
            result = strategy(error)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "reason": str(e)
            }
    
    def get_error_history(
        self,
        limit: int = 50,
        severity: ErrorSeverity = None,
        category: ErrorCategory = None
    ) -> List[Dict]:
        """
        Get error history with optional filters.
        
        Args:
            limit: Maximum number of errors to return
            severity: Filter by severity (optional)
            category: Filter by category (optional)
        
        Returns:
            List of error records
        """
        if not self.error_log.exists():
            return []
        
        errors = []
        try:
            with open(self.error_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        error = json.loads(line.strip())
                        
                        # Apply filters
                        if severity and error.get("severity") != severity.value:
                            continue
                        if category and error.get("category") != category.value:
                            continue
                        
                        errors.append(error)
                    except json.JSONDecodeError:
                        continue
        except IOError as e:
            self.logger.error(f"Failed to read error log: {e}")
        
        return errors[-limit:]
    
    def clear_error_log(self):
        """Clear error log file"""
        if self.error_log.exists():
            self.error_log.unlink()
            self.logger.info("Error log cleared")


# ============================================
# Retry Mechanism
# ============================================

def retry_on_error(
    max_retries: int = 3,
    delay_seconds: float = 5.0,
    backoff_multiplier: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (PipelineError,),
    on_retry: Callable = None
):
    """
    Decorator for automatic retry on errors.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay_seconds: Initial delay between retries
        backoff_multiplier: Multiply delay by this after each retry
        exceptions: Tuple of exception types to catch
        on_retry: Callback function called on each retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            current_delay = delay_seconds
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_error = e
                    
                    # Check if error is recoverable
                    if isinstance(e, PipelineError):
                        if not e.recoverable:
                            raise
                        
                        # Update retry count
                        e.retry_count = attempt
                    
                    # Last attempt - raise the error
                    if attempt == max_retries:
                        raise
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    # Wait before retry
                    time.sleep(current_delay)
                    current_delay *= backoff_multiplier
            
            # Should not reach here, but just in case
            raise last_error
        
        return wrapper
    return decorator


class RetryStrategy:
    """Configurable retry strategy"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_backoff: bool = True,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_backoff = exponential_backoff
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        import random
        
        if self.exponential_backoff:
            delay = self.base_delay * (2 ** attempt)
        else:
            delay = self.base_delay
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter (random 0-25% of delay)
        if self.jitter:
            delay *= (1 + random.random() * 0.25)
        
        return delay
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        on_retry: Callable = None,
        **kwargs
    ):
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            on_retry: Callback called on each retry
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of func
        
        Raises:
            Last exception if all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                
                # Check if we should retry
                if attempt == self.max_retries:
                    raise
                
                if isinstance(e, PipelineError) and not e.recoverable:
                    raise
                
                # Callback
                if on_retry:
                    on_retry(attempt + 1, e)
                
                # Wait
                time.sleep(self.get_delay(attempt))
        
        raise last_error


# ============================================
# Common Error Scenarios
# ============================================

# Pre-defined error codes
ERROR_CODES = {
    # AI Errors
    "AI_RATE_LIMIT": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": True,
        "message": "AI API rate limit exceeded"
    },
    "AI_TIMEOUT": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": True,
        "message": "AI API request timeout"
    },
    "AI_INVALID_RESPONSE": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": True,
        "message": "AI returned invalid response"
    },
    "AI_AUTH_FAILED": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": False,
        "message": "AI API authentication failed"
    },
    "AI_MODEL_NOT_FOUND": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": False,
        "message": "AI model not found"
    },
    
    # Network Errors
    "NETWORK_ERROR": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": True,
        "message": "Network connection error"
    },
    "NETWORK_TIMEOUT": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": True,
        "message": "Network request timeout"
    },
    
    # File Errors
    "FILE_NOT_FOUND": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": False,
        "message": "File not found"
    },
    "FILE_PERMISSION": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": False,
        "message": "File permission denied"
    },
    "FILE_WRITE_ERROR": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": True,
        "message": "Failed to write file"
    },
    
    # Validation Errors
    "VALIDATION_FAILED": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": False,
        "message": "Validation failed"
    },
    "INVALID_INPUT": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": False,
        "message": "Invalid input"
    },
    
    # State Errors
    "STATE_NOT_FOUND": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": False,
        "message": "Pipeline state not found"
    },
    "STATE_CORRUPTED": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": False,
        "message": "Pipeline state corrupted"
    },
    
    # Step Errors
    "STEP_DEPENDENCY": {
        "severity": ErrorSeverity.HIGH,
        "recoverable": True,
        "message": "Step dependency not satisfied"
    },
    "STEP_TIMEOUT": {
        "severity": ErrorSeverity.MEDIUM,
        "recoverable": True,
        "message": "Step execution timeout"
    }
}


def create_error(code: str, **kwargs) -> PipelineError:
    """
    Create a PipelineError from predefined error code.
    
    Args:
        code: Error code from ERROR_CODES
        **kwargs: Additional arguments for error
    
    Returns:
        PipelineError instance
    """
    if code not in ERROR_CODES:
        return PipelineError(
            message=f"Unknown error code: {code}",
            code=code
        )
    
    error_def = ERROR_CODES[code]
    
    return PipelineError(
        message=kwargs.pop("message", error_def["message"]),
        code=code,
        severity=kwargs.pop("severity", error_def["severity"]),
        recoverable=kwargs.pop("recoverable", error_def["recoverable"]),
        **kwargs
    )
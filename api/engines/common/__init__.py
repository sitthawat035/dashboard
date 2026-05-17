# Common Shared Modules
# This package contains shared utilities for all subprojects

from .utils import setup_logger, get_date_str, ensure_dir, sanitize_filename
from .config import Config
from .ai_client import create_ai_client, GeminiClient
from .facebook_api import post_to_facebook

# Browser is optional (requires playwright)
try:
    from .browser import create_browser_manager
except ImportError:
    create_browser_manager = None

# Pipeline modules
from .state_manager import StateManager, PipelineStatus, StepStatus
from .error_handler import (
    ErrorHandler, PipelineError, AIError, NetworkError, 
    ValidationError, FileError, StateError,
    ErrorSeverity, ErrorCategory, RetryStrategy, retry_on_error
)
from .pipeline_base import (
    BaseStep, BasePipeline, StepResult, PipelineMode,
    create_step_decorator
)

__all__ = [
    # Utils
    'setup_logger',
    'get_date_str', 
    'ensure_dir',
    'sanitize_filename',
    
    # Config
    'Config',
    
    # AI Client
    'create_ai_client',
    'GeminiClient',
    
    # Facebook API
    'post_to_facebook',
    
    # Browser
    'create_browser_manager',
    
    # State Management
    'StateManager',
    'PipelineStatus',
    'StepStatus',
    
    # Error Handling
    'ErrorHandler',
    'PipelineError',
    'AIError',
    'NetworkError',
    'ValidationError',
    'FileError',
    'StateError',
    'ErrorSeverity',
    'ErrorCategory',
    'RetryStrategy',
    'retry_on_error',
    
    # Pipeline Base
    'BaseStep',
    'BasePipeline',
    'StepResult',
    'PipelineMode',
    'create_step_decorator',
]

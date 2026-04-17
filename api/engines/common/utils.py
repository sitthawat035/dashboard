import os
import re
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import io

# Configure logging with UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


# Colors for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def setup_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """Set up and return a logger instance with optional file handler."""
    logger = logging.getLogger(name)
    if log_file is not None:
        try:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(str(log_file), encoding="utf-8")
            fh.setLevel(logging.ERROR)
            fh.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(fh)
        except Exception:
            pass  # Silently ignore file handler errors
    return logger


def get_timestamp() -> str:
    """Return formatted timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_date_str() -> str:
    """Return YYYY-MM-DD string."""
    return datetime.now().strftime("%Y-%m-%d")


def ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load JSON file safely."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Error loading JSON from {path}: {e}")
        return {}


# Alias for compatibility with config.py
load_json = load_json_file


def save_json_file(path: Path, data: Any) -> None:
    """Save data to JSON file."""
    ensure_dir(path.parent)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print_error(f"Error saving JSON to {path}: {e}")


def load_markdown(path: Path) -> str:
    """Load markdown file content."""
    if not path.exists():
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print_error(f"Error loading markdown from {path}: {e}")
        return ""


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Sanitize string to be safe for filenames."""
    # Remove invalid char
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    # Replace spaces with underscore
    name = name.replace(" ", "_")
    # Limit length
    if len(name) > max_length:
        name = name[:max_length]
    return name


def safe_print(text: str, fallback_text: Optional[str] = None) -> None:
    """Print text safely, falling back if encoding fails (Windows fix)."""
    try:
        print(text)
    except UnicodeEncodeError:
        # If printing emoji fails, print fallback or stripped version
        if fallback_text:
            try:
                print(fallback_text)
            except UnicodeEncodeError:
                # Last resort: strip non-ascii
                print(fallback_text.encode("ascii", "ignore").decode("ascii"))
        else:
            # Strip non-ascii characters
            print(text.encode("ascii", "ignore").decode("ascii"))


def print_header(text: str) -> None:
    safe_print(f"\n{Colors.HEADER}=== {text} ==={Colors.ENDC}", f"\n=== {text} ===")


def print_success(text: str) -> None:
    safe_print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}", f"[SUCCESS] {text}")


def print_info(text: str) -> None:
    safe_print(f"{Colors.OKBLUE}ℹ️ {text}{Colors.ENDC}", f"[INFO] {text}")


def print_warning(text: str) -> None:
    safe_print(f"{Colors.WARNING}⚠️ {text}{Colors.ENDC}", f"[WARN] {text}")


def print_error(text: str) -> None:
    safe_print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}", f"[ERROR] {text}")
